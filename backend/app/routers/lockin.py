"""Lock-in amplifier control endpoints."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends

from app.core.lockin import SR865A
from app.dependencies import get_executor, get_lockin
from app.models.lockin import LockinSensitivityRequest, LockinTimeConstantRequest

router = APIRouter()


@router.get("/lockin/settings")
async def get_lockin_settings(
    lockin: SR865A = Depends(get_lockin),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        settings = await asyncio.get_running_loop().run_in_executor(
            executor,
            lambda: {
                "sensitivity": lockin.get_sensitivity(),
                "time_constant": lockin.get_time_constant(),
            },
        )
        return {
            "status": "success",
            "sensitivity": settings["sensitivity"],
            "time_constant": settings["time_constant"],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/lockin/sensitivity")
async def change_lockin_sensitivity(
    params: LockinSensitivityRequest,
    lockin: SR865A = Depends(get_lockin),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        current_sensitivity = await asyncio.get_running_loop().run_in_executor(
            executor, lambda: lockin.get_sensitivity()
        )
        new_sensitivity = current_sensitivity + (1 if params.increment else -1)
        if 0 <= new_sensitivity <= 27:
            await asyncio.get_running_loop().run_in_executor(
                executor, lambda: lockin.set_sensitivity(new_sensitivity)
            )
            return {"status": "success", "sensitivity": new_sensitivity}
        else:
            return {"status": "error", "message": "Sensitivity out of range"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/lockin/time_constant")
async def change_lockin_time_constant(
    params: LockinTimeConstantRequest,
    lockin: SR865A = Depends(get_lockin),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        current_time_constant = await asyncio.get_running_loop().run_in_executor(
            executor, lambda: lockin.get_time_constant()
        )
        new_time_constant = current_time_constant + (1 if params.increment else -1)
        if 0 <= new_time_constant <= 23:
            await asyncio.get_running_loop().run_in_executor(
                executor,
                lambda: lockin.set_time_constant(new_time_constant),
            )
            return {"status": "success", "time_constant": new_time_constant}
        else:
            return {"status": "error", "message": "Time constant out of range"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
