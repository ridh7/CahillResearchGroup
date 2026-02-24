"""FD-PBD analysis endpoints."""

import json
import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.anisotropic_analysis import run_anisotropic_analysis
from app.core.fdpbd_analysis import run_fdpbd_analysis
from app.core.transverse_isotropic_analysis import run_transverse_isotropic_analysis
from app.models.fdpbd import FDPBDParams, FDPBDResult
from app.models.models import AnisotropicFDPBDParams, AnisotropicFDPBDResult
from app.models.transverse_isotropic import (
    TransverseIsotropicParams,
    TransverseIsotropicResult,
)

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
