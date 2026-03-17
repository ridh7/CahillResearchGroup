"""FD-PBD analysis endpoints."""

import asyncio
import contextlib
import json
import os
import queue
import tempfile
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.anisotropic_analysis import (
    run_anisotropic_analysis,
    run_de_fitting_anisotropic,
)
from app.core.fdpbd_analysis import run_fdpbd_analysis
from app.core.transverse_isotropic_analysis import (
    run_de_fitting_transverse,
    run_transverse_isotropic_analysis,
)
from app.models.fdpbd import FDPBDParams, FDPBDResult
from app.models.models import AnisotropicFDPBDParams, AnisotropicFDPBDResult
from app.models.transverse_isotropic import (
    TransverseIsotropicParams,
    TransverseIsotropicResult,
)

_fit_executor = ThreadPoolExecutor(max_workers=1)

router = APIRouter()


async def analyze_fdpbd(params: FDPBDParams, file: UploadFile) -> FDPBDResult:
    """Helper function to process FD-PBD analysis."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", dir="data") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = run_fdpbd_analysis(
            params, os.path.basename(tmp_path).replace(".txt", "")
        )
        return FDPBDResult(**result)
    finally:
        os.unlink(tmp_path)


async def analyze_anisotropic(params: dict, file: UploadFile) -> AnisotropicFDPBDResult:
    """Helper function to process anisotropic FD-PBD analysis."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", dir="data") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = run_anisotropic_analysis(
            params, os.path.basename(tmp_path).replace(".txt", "")
        )
        return AnisotropicFDPBDResult(**result)
    finally:
        os.unlink(tmp_path)


@router.post("/fdpbd/analyze", response_model=FDPBDResult)
async def fdpbd_analyze(params: str = Form(...), file: UploadFile = File(...)):
    """Analyze FD-PBD data with given parameters and uploaded file."""
    try:
        # Parse params string as JSON
        params_dict = json.loads(params)
        # Convert eta_down from comma-separated string to list of floats
        if isinstance(params_dict.get("eta_down"), str):
            params_dict["eta_down"] = [
                float(x) for x in params_dict["eta_down"].split(",") if x.strip()
            ]
        # Validate with FDPBDParams
        validated_params = FDPBDParams(**params_dict)
        result = await analyze_fdpbd(validated_params, file)
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format in params"
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid eta_down format: {str(e)}"
        ) from e
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def analyze_transverse_isotropic(
    params: TransverseIsotropicParams, file: UploadFile
) -> TransverseIsotropicResult:
    """Helper function to process transversely isotropic FD-PBD analysis."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", dir="data") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = run_transverse_isotropic_analysis(
            params, os.path.basename(tmp_path).replace(".txt", "")
        )
        return TransverseIsotropicResult(**result)
    finally:
        os.unlink(tmp_path)


@router.post("/fdpbd/analyze_anisotropy", response_model=AnisotropicFDPBDResult)
async def fdpbd_analyze_anisotropic(
    params: str = Form(...), file: UploadFile = File(...)
):
    """Analyze anisotropic FD-PBD data with given parameters and uploaded file."""
    try:
        params_dict = json.loads(params)
        validated_params = AnisotropicFDPBDParams(**params_dict)
        result = await analyze_anisotropic(validated_params.dict(), file)
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format in params"
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid parameter format: {str(e)}"
        ) from e
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/fdpbd/fit_anisotropy")
async def fit_anisotropy_sse(params: str = Form(...), file: UploadFile = File(...)):
    """Run DE fitting for anisotropic mode, streaming progress via SSE."""
    params_dict = json.loads(params)
    fit_param = params_dict.pop("fit_parameter")
    bounds_min = float(params_dict.pop("fit_bounds_min"))
    bounds_max = float(params_dict.pop("fit_bounds_max"))
    maxiter = int(params_dict.pop("fit_maxiter", 20))
    popsize = int(params_dict.pop("fit_popsize", 8))
    tol = float(params_dict.pop("fit_tol", 1e-3))

    validated_params = AnisotropicFDPBDParams(**params_dict)

    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", dir="data") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    data_filename = os.path.basename(tmp_path).replace(".txt", "")
    progress_queue: queue.Queue = queue.Queue()

    def run_fit():
        try:
            result = run_de_fitting_anisotropic(
                validated_params.dict(),
                data_filename,
                fit_param,
                (bounds_min, bounds_max),
                progress_callback=lambda d: progress_queue.put(d),
                maxiter=maxiter,
                popsize=popsize,
                tol=tol,
            )
            progress_queue.put(result)
        except Exception as e:
            progress_queue.put({"type": "error", "message": str(e)})
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)

    _fit_executor.submit(run_fit)

    async def event_generator():
        while True:
            try:
                data = progress_queue.get_nowait()
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("type") in ("result", "error"):
                    break
            except queue.Empty:
                # Send SSE comment as heartbeat to keep connection alive and flush
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/fdpbd/analyze_transverse", response_model=TransverseIsotropicResult)
async def fdpbd_analyze_transverse(
    params: str = Form(...), file: UploadFile = File(...)
):
    """Analyze transversely isotropic FD-PBD data with given parameters and uploaded file."""
    try:
        params_dict = json.loads(params)
        validated_params = TransverseIsotropicParams(**params_dict)
        result = await analyze_transverse_isotropic(validated_params, file)
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format in params"
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid parameter format: {str(e)}"
        ) from e
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/fdpbd/fit_transverse")
async def fit_transverse_sse(params: str = Form(...), file: UploadFile = File(...)):
    """Run DE fitting for transverse isotropic mode, streaming progress via SSE."""
    params_dict = json.loads(params)
    fit_param = params_dict.pop("fit_parameter")
    bounds_min = float(params_dict.pop("fit_bounds_min"))
    bounds_max = float(params_dict.pop("fit_bounds_max"))
    maxiter = int(params_dict.pop("fit_maxiter", 20))
    popsize = int(params_dict.pop("fit_popsize", 8))
    tol = float(params_dict.pop("fit_tol", 1e-3))

    validated_params = TransverseIsotropicParams(**params_dict)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", dir="data") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    data_filename = os.path.basename(tmp_path).replace(".txt", "")
    progress_queue: queue.Queue = queue.Queue()

    def run_fit():
        try:
            result = run_de_fitting_transverse(
                validated_params,
                data_filename,
                fit_param,
                (bounds_min, bounds_max),
                progress_callback=lambda d: progress_queue.put(d),
                maxiter=maxiter,
                popsize=popsize,
                tol=tol,
            )
            progress_queue.put(result)
        except Exception as e:
            progress_queue.put({"type": "error", "message": str(e)})
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)

    _fit_executor.submit(run_fit)

    async def event_generator():
        while True:
            try:
                data = progress_queue.get_nowait()
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("type") in ("result", "error"):
                    break
            except queue.Empty:
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
