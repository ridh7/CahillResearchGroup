"""Stage control endpoints for Thorlabs motorized stage."""

import asyncio
import os
import queue
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends
from System import Decimal

from app.core.stage import ThorlabsBBD302
from app.dependencies import get_executor, get_stage, get_stage_optional
from app.models.channel import ChannelParams, Settings
from app.models.stage import MovementParams, ScanParams
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


@router.post("/start")
async def start_movement(
    params: ScanParams,
    stage: ThorlabsBBD302 = Depends(get_stage),
):
    """
    Unified scan endpoint. Routes to step-and-measure or continuous scan
    based on motion_type parameter.

    Returns immediately with {"status": "started"} — scan runs in a daemon
    thread so uvicorn can reload/shutdown without waiting for the scan to finish.
    Scan completion is signalled via the /ws/scan_data WebSocket.
    """
    # Resolve step sizes before launching the thread so we can return errors
    # synchronously without the thread needing to communicate them back.
    slow_step: float | None = None
    fast_step: float | None = None
    if params.motion_type == "continuous":
        slow_step = (
            params.x_step_size if params.fast_axis == "y" else params.y_step_size
        )
        if slow_step is None:
            if params.fast_axis == "y" and params.x_steps:
                slow_step = abs(params.x2 - params.x1) / params.x_steps
            elif params.fast_axis == "x" and params.y_steps:
                slow_step = abs(params.y2 - params.y1) / params.y_steps
            else:
                return {
                    "status": "error",
                    "message": "Slow axis step size required for continuous scan",
                }
        fast_step = (
            params.y_step_size if params.fast_axis == "y" else params.x_step_size
        )
        if fast_step is None:
            if params.fast_axis == "y" and params.y_steps:
                fast_step = abs(params.y2 - params.y1) / params.y_steps
            elif params.fast_axis == "x" and params.x_steps:
                fast_step = abs(params.x2 - params.x1) / params.x_steps

    # Increment the scan generation so any still-running previous scan thread
    # sees the mismatch and exits immediately (without waiting for scan_active).
    global_state.scan_generation += 1
    my_generation = global_state.scan_generation

    # Set scan_active early so the WebSocket handler knows a scan is starting
    # (prevents race condition where WS connects before scan thread sets it)
    global_state.scan_active = True
    global_state.scan_data_queue = queue.Queue()

    def _run_scan() -> None:
        try:
            if params.motion_type == "continuous":
                stage.continuous_scan(
                    params.x1,
                    params.y1,
                    params.x2,
                    params.y2,
                    slow_step,
                    params.scan_pattern,
                    params.record_retrace,
                    params.fast_axis,
                    fast_step,
                    params.sample_id,
                    params.comments,
                    params.save_dir,
                    scan_generation=my_generation,
                )
            else:
                stage.move_in_rectangle(
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
                    params.scan_pattern,
                    params.fast_axis,
                    params.sample_id,
                    params.comments,
                    params.save_dir,
                )
        except Exception as e:
            print(f"---Scan thread error: {e}")
            traceback.print_exc()
            global_state.scan_active = False

    # Daemon thread: killed automatically when the process exits (e.g. on hot-reload),
    # so uvicorn can restart without being blocked by a long-running scan.
    threading.Thread(target=_run_scan, daemon=True, name="scan-thread").start()
    return {"status": "started"}


@router.post("/stop")
async def stop_motion(
    stage: ThorlabsBBD302 = Depends(get_stage),
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    """Immediately stop all stage motion and abort any running scan."""
    global_state.scan_active = False
    try:
        await asyncio.get_running_loop().run_in_executor(executor, lambda: stage.stop())
        return {"status": "success", "message": "Motion stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/default-save-dir")
async def default_save_dir():
    """Return the backend's current working directory (the default save location)."""
    return {"directory": os.getcwd()}


@router.get("/choose-save-dir")
async def choose_save_dir(
    initialdir: str = "",
    executor: ThreadPoolExecutor = Depends(get_executor),
):
    """Show a native OS folder-picker dialog and return the chosen directory."""

    def _show_dialog():
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        directory = filedialog.askdirectory(
            title="Choose save folder...",
            initialdir=initialdir or os.getcwd(),
        )
        root.destroy()
        return directory or ""

    directory = await asyncio.get_running_loop().run_in_executor(executor, _show_dialog)
    return {"directory": directory}


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
                lambda: stage.home_all(),
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
