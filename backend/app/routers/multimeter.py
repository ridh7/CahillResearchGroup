"""Multimeter control endpoints."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends

from app.core.multimeter import BKPrecision5493C
from app.dependencies import get_executor, get_multimeter
from app.models.multimeter import MultimeterApertureRequest, MultimeterTerminalRequest
from app.models.state import global_state

router = APIRouter()


@router.get("/multimeter/settings")
async def get_multimeter_settings(
    multimeter: BKPrecision5493C = Depends(get_multimeter),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        settings = await asyncio.get_running_loop().run_in_executor(
            executor,
            lambda: {
                "aperture": multimeter.get_aperture(),
                "terminal": multimeter.get_terminal(),
            },
        )
        return {
            "status": "success",
            "aperture": settings["aperture"],
            "terminal": settings["terminal"],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/multimeter/aperture")
async def set_multimeter_aperture(
    params: MultimeterApertureRequest,
    multimeter: BKPrecision5493C = Depends(get_multimeter),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        global_state.pause_multimeter_reading.set()
        success = await asyncio.get_running_loop().run_in_executor(
            executor, lambda: multimeter.set_aperture(params.nplc)
        )
        if success:
            return {"status": "success", "aperture": params.nplc}
        else:
            return {"status": "error", "message": "Failed to set aperture"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        global_state.pause_multimeter_reading.clear()


@router.post("/multimeter/terminal")
async def set_multimeter_terminal(
    params: MultimeterTerminalRequest,
    multimeter: BKPrecision5493C = Depends(get_multimeter),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        global_state.pause_multimeter_reading.set()
        success = await asyncio.get_running_loop().run_in_executor(
            executor, lambda: multimeter.set_terminal(params.terminal)
        )
        if success:
            return {"status": "success", "terminal": params.terminal}
        else:
            return {"status": "error", "message": "Failed to set terminal"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        global_state.pause_multimeter_reading.clear()
