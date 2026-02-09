"""Stage control endpoints for Thorlabs motorized stage."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends
from System import Decimal

from app.core.stage import ThorlabsBBD302
from app.dependencies import get_executor, get_stage, get_stage_optional
from app.models.channel import ChannelParams, Settings
from app.models.stage import MoveAndLogParams, MovementParams, RectangleParams
from app.models.state import global_state

router = APIRouter()


@router.post("/move")
async def move(
    params: MovementParams,
    stage: ThorlabsBBD302 = Depends(get_stage),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    """Move stage to absolute (X, Y) position in mm."""
    try:
        await asyncio.get_running_loop().run_in_executor(
            executor, lambda: stage.move(params.x, params.y)
        )
        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/move_and_log")
async def move_and_log(
    params: MoveAndLogParams,
    stage: ThorlabsBBD302 = Depends(get_stage),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    """
    Perform bidirectional zigzag scan with continuous data logging.

    Scans from current position to (x, y) in a raster pattern,
    logging instrument data at specified sample_rate during motion.
    Saves results to timestamped CSV file in data/ directory.
    """
    try:
        await asyncio.get_running_loop().run_in_executor(
            executor,
            lambda: stage.move_and_log(
                params.x, params.y, params.x_step_size, params.sample_rate
            ),
        )
        return {"status": "success", "message": "Movement and logging completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/start")
async def start_movement(
    params: RectangleParams,
    stage: ThorlabsBBD302 = Depends(get_stage),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    """
    Perform unidirectional rectangular grid scan (legacy endpoint).

    Scans rectangular region with uniform X/Y steps, pausing at each point
    to collect measurements. Closes all WebSocket connections after completion
    to signal end of scan. Superseded by /move_and_log for faster scanning.
    """
    try:
        future = asyncio.get_running_loop().run_in_executor(
            executor,
            lambda: stage.move_in_rectangle(
                params.x1,
                params.y1,
                params.x2,
                params.y2,
                params.x_steps,
                params.y_steps,
                params.x_step_size,
                params.y_step_size,
                params.movement_mode,
                params.delay,
            ),
        )
        await future
        for ws in [
            global_state.ws_lockin,
            global_state.ws_multimeter,
            global_state.ws_stage,
        ]:
            if ws is not None:
                try:
                    await ws.close()
                    ws = None
                except Exception as e:
                    print(f"Error closing {ws} websocket: {e}")
        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
        for ws in [
            global_state.ws_lockin,
            global_state.ws_multimeter,
            global_state.ws_stage,
        ]:
            if ws is not None:
                try:
                    await ws.close()
                    ws = None
                except Exception as close_error:
                    print(f"Error closing {ws} websocket: {close_error}")
        return {"status": "error", "message": str(e)}


@router.post("/home")
async def home(
    params: ChannelParams,
    stage: ThorlabsBBD302 = Depends(get_stage),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        if params.channel_direction == "x":
            await asyncio.get_running_loop().run_in_executor(
                executor, lambda: stage.home_channel(1)
            )
        elif params.channel_direction == "y":
            await asyncio.get_running_loop().run_in_executor(
                executor, lambda: stage.home_channel(2)
            )
        else:
            await asyncio.get_running_loop().run_in_executor(
                executor,
                lambda: (
                    stage.home_channel(1),
                    stage.home_channel(2),
                ),
            )
        return {"status": "success", "message": "Homing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/get_movement_params")
async def get_movement_params_api(
    stage: ThorlabsBBD302 = Depends(get_stage),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        params = await asyncio.get_running_loop().run_in_executor(
            executor,
            lambda: (
                stage.get_movement_params(1),
                stage.get_movement_params(2),
            ),
        )
        home_params_x, vel_params_x = params[0]
        home_params_y, vel_params_y = params[1]
        return {
            "status": "success",
            "homing_velocity_x": f"{home_params_x.Velocity}",
            "max_velocity_x": f"{vel_params_x.MaxVelocity}",
            "acceleration_x": f"{vel_params_x.Acceleration}",
            "homing_velocity_y": f"{home_params_y.Velocity}",
            "max_velocity_y": f"{vel_params_y.MaxVelocity}",
            "acceleration_y": f"{vel_params_y.Acceleration}",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/set_movement_params")
async def set_movement_params_api(
    params: Settings,
    stage: ThorlabsBBD302 = Depends(get_stage),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    try:
        await asyncio.get_running_loop().run_in_executor(
            executor,
            lambda: (
                stage.channel[1].SetHomingVelocity(
                    Decimal(params.channel1.homing_velocity)
                ),
                stage.channel[1].SetVelocityParams(
                    Decimal(params.channel1.max_velocity),
                    Decimal(params.channel1.acceleration),
                ),
                stage.channel[2].SetHomingVelocity(
                    Decimal(params.channel2.homing_velocity)
                ),
                stage.channel[2].SetVelocityParams(
                    Decimal(params.channel2.max_velocity),
                    Decimal(params.channel2.acceleration),
                ),
            ),
        )
        print("---Movement params set")
        return {"status": "success", "message": "movement params set"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/get_current_position")
async def get_current_position(
    stage: ThorlabsBBD302 | None = Depends(get_stage_optional),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    """
    Get current stage position.

    Returns error dict with NaN values instead of 503 to maintain
    frontend compatibility (displays position even when unavailable).
    """
    if stage is None:
        return {"status": "error", "x": "NaN", "y": "NaN"}
    try:
        position = await asyncio.get_running_loop().run_in_executor(
            executor,
            lambda: (
                stage.channel[1].DevicePosition,
                stage.channel[2].DevicePosition,
            ),
        )
        return {"status": "success", "x": f"{position[0]}", "y": f"{position[1]}"}
    except Exception:
        return {"status": "error", "x": "NaN", "y": "NaN"}
