import asyncio
import json
import os
import queue
import tempfile
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from System import Decimal

from app.core.anisotropic_analysis import run_anisotropic_analysis
from app.core.fdpbd_analysis import run_fdpbd_analysis
from app.core.shared_state import shared_state
from app.models.channel import ChannelParams, Settings
from app.models.fdpbd import FDPBDParams, FDPBDResult
from app.models.lockin import (
    LockinFilterSlopeRequest,
    LockinFrequencyRequest,
    LockinSensitivityRequest,
    LockinTimeConstantRequest,
)
from app.models.models import (
    AnisotropicFDPBDParams,
    AnisotropicFDPBDResult,
)
from app.models.multimeter import MultimeterApertureRequest, MultimeterTerminalRequest
from app.models.stage import (
    MovementParams,
    ScanParams,
)
from app.models.state import global_state

router = APIRouter()
executor = ThreadPoolExecutor()


@router.post("/move")
async def move(params: MovementParams):
    """Move stage to absolute (X, Y) position in mm."""
    if global_state.stage is None:
        raise HTTPException(status_code=503, detail="Stage not initialized")
    stage = global_state.stage  # Capture reference for type narrowing
    try:
        await asyncio.get_event_loop().run_in_executor(
            executor, lambda: stage.move(params.x, params.y)
        )
        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/start")
async def start_movement(params: ScanParams):
    """
    Unified scan endpoint. Routes to step-and-measure or continuous scan
    based on motion_type parameter.

    Returns immediately with {"status": "started"} — scan runs in a daemon
    thread so uvicorn can reload/shutdown without waiting for the scan to finish.
    Scan completion is signalled via the /ws/scan_data WebSocket.
    """
    if global_state.stage is None:
        raise HTTPException(status_code=503, detail="Stage not initialized")
    stage = global_state.stage

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

    # Increment the scan generation so any still-running previous scan thread
    # sees the mismatch and exits immediately (without waiting for scan_active).
    shared_state.scan_generation += 1
    my_generation = shared_state.scan_generation

    # Set scan_active early so the WebSocket handler knows a scan is starting
    # (prevents race condition where WS connects before scan thread sets it)
    shared_state.scan_active = True
    shared_state.scan_data_queue = queue.Queue()

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
            shared_state.scan_active = False

    # Daemon thread: killed automatically when the process exits (e.g. on hot-reload),
    # so uvicorn can restart without being blocked by a long-running scan.
    threading.Thread(target=_run_scan, daemon=True, name="scan-thread").start()
    return {"status": "started"}


@router.get("/default-save-dir")
async def default_save_dir():
    """Return the backend's current working directory (the default save location)."""
    return {"directory": os.getcwd()}


@router.get("/choose-save-dir")
async def choose_save_dir(initialdir: str = ""):
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

    directory = await asyncio.get_event_loop().run_in_executor(executor, _show_dialog)
    return {"directory": directory}


@router.post("/stop")
async def stop_motion():
    """Immediately stop all stage motion and abort any running scan."""
    if global_state.stage is None:
        raise HTTPException(status_code=503, detail="Stage not initialized")
    stage = global_state.stage
    shared_state.scan_active = False
    try:
        await asyncio.get_event_loop().run_in_executor(executor, lambda: stage.stop())
        return {"status": "success", "message": "Motion stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/home")
async def home(params: ChannelParams):
    if global_state.stage is None:
        raise HTTPException(status_code=503, detail="Stage not initialized")
    stage = global_state.stage  # Capture reference for type narrowing
    try:
        if params.channel_direction == "x":
            await asyncio.get_event_loop().run_in_executor(
                executor, lambda: stage.home_channel(1)
            )
        elif params.channel_direction == "y":
            await asyncio.get_event_loop().run_in_executor(
                executor, lambda: stage.home_channel(2)
            )
        else:
            await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: stage.home_all(),
            )
        return {"status": "success", "message": "Homing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/get_movement_params")
async def get_movement_params_api():
    if global_state.stage is None:
        raise HTTPException(status_code=503, detail="Stage not initialized")
    stage = global_state.stage  # Capture reference for type narrowing
    try:
        params = await asyncio.get_event_loop().run_in_executor(
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
async def set_movement_params_api(params: Settings):
    if global_state.stage is None:
        raise HTTPException(status_code=503, detail="Stage not initialized")
    stage = global_state.stage  # Capture reference for type narrowing
    try:
        await asyncio.get_event_loop().run_in_executor(
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
async def get_current_position():
    if global_state.stage is None:
        return {"status": "error", "x": "NaN", "y": "NaN"}
    stage = global_state.stage  # Capture reference for type narrowing
    try:
        position = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: (
                stage.channel[1].DevicePosition,
                stage.channel[2].DevicePosition,
            ),
        )
        return {"status": "success", "x": f"{position[0]}", "y": f"{position[1]}"}
    except Exception:
        return {"status": "error", "x": "NaN", "y": "NaN"}


@router.get("/lockin/settings")
async def get_lockin_settings():
    if global_state.lockin is None:
        raise HTTPException(status_code=503, detail="Lock-in amplifier not initialized")
    lockin = global_state.lockin  # Capture reference for type narrowing
    try:
        settings = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: {
                "sensitivity": lockin.get_sensitivity(),
                "time_constant": lockin.get_time_constant(),
                "frequency": lockin.get_frequency(),
                "filter_slope": lockin.get_filter_slope(),
            },
        )
        return {
            "status": "success",
            "sensitivity": settings["sensitivity"],
            "time_constant": settings["time_constant"],
            "frequency": settings["frequency"],
            "filter_slope": settings["filter_slope"],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/lockin/sensitivity")
async def change_lockin_sensitivity(params: LockinSensitivityRequest):
    if global_state.lockin is None:
        raise HTTPException(status_code=503, detail="Lock-in amplifier not initialized")
    lockin = global_state.lockin  # Capture reference for type narrowing
    try:
        current_sensitivity = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: lockin.get_sensitivity()
        )
        new_sensitivity = current_sensitivity + (1 if params.increment else -1)
        if 0 <= new_sensitivity <= 27:
            await asyncio.get_event_loop().run_in_executor(
                executor, lambda: lockin.set_sensitivity(new_sensitivity)
            )
            return {"status": "success", "sensitivity": new_sensitivity}
        else:
            return {"status": "error", "message": "Sensitivity out of range"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/lockin/time_constant")
async def change_lockin_time_constant(params: LockinTimeConstantRequest):
    if global_state.lockin is None:
        raise HTTPException(status_code=503, detail="Lock-in amplifier not initialized")
    lockin = global_state.lockin  # Capture reference for type narrowing
    try:
        current_time_constant = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: lockin.get_time_constant()
        )
        new_time_constant = current_time_constant + (1 if params.increment else -1)
        if 0 <= new_time_constant <= 23:
            await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: lockin.set_time_constant(new_time_constant),
            )
            return {"status": "success", "time_constant": new_time_constant}
        else:
            return {"status": "error", "message": "Time constant out of range"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/lockin/frequency")
async def set_lockin_frequency(params: LockinFrequencyRequest):
    if global_state.lockin is None:
        raise HTTPException(status_code=503, detail="Lock-in amplifier not initialized")
    lockin = global_state.lockin
    try:
        await asyncio.get_event_loop().run_in_executor(
            executor, lambda: lockin.set_frequency(params.frequency)
        )
        return {"status": "success", "frequency": params.frequency}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/lockin/filter_slope")
async def set_lockin_filter_slope(params: LockinFilterSlopeRequest):
    if global_state.lockin is None:
        raise HTTPException(status_code=503, detail="Lock-in amplifier not initialized")
    lockin = global_state.lockin
    try:
        await asyncio.get_event_loop().run_in_executor(
            executor, lambda: lockin.set_filter_slope(params.code)
        )
        return {"status": "success", "filter_slope": params.code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/multimeter/settings")
async def get_multimeter_settings():
    if global_state.multimeter is None:
        raise HTTPException(status_code=503, detail="Multimeter not initialized")
    multimeter = global_state.multimeter  # Capture reference for type narrowing
    try:
        settings = await asyncio.get_event_loop().run_in_executor(
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
async def set_multimeter_aperture(params: MultimeterApertureRequest):
    if global_state.multimeter is None:
        raise HTTPException(status_code=503, detail="Multimeter not initialized")
    multimeter = global_state.multimeter  # Capture reference for type narrowing
    try:
        success = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: multimeter.set_aperture(params.nplc)
        )
        if success:
            return {"status": "success", "aperture": params.nplc}
        else:
            return {"status": "error", "message": "Failed to set aperture"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/multimeter/terminal")
async def set_multimeter_terminal(params: MultimeterTerminalRequest):
    if global_state.multimeter is None:
        raise HTTPException(status_code=503, detail="Multimeter not initialized")
    multimeter = global_state.multimeter  # Capture reference for type narrowing
    try:
        success = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: multimeter.set_terminal(params.terminal)
        )
        if success:
            return {"status": "success", "terminal": params.terminal}
        else:
            return {"status": "error", "message": "Failed to set terminal"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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


@router.get("/")
def read_root():
    return {"status": "API is running"}
