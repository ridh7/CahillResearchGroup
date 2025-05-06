from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from concurrent.futures import ThreadPoolExecutor
import asyncio
from app.models.stage import *
from app.models.channel import *
from app.models.lockin import *
from app.models.multimeter import *
from app.models.state import global_state
from app.models.fdpbd import FDPBDParams, FDPBDResult
from app.services.fdpbd_service import analyze_fdpbd
from app.core.fdpbd_analysis import run_fdpbd_analysis
from app.core.anisotropic_analysis import run_anisotropic_analysis
from app.models.models import (
    AnisotropicFDPBDParams,
    AnisotropicFDPBDResult,
)
import clr
from System import Decimal
import json
import tempfile
import os

router = APIRouter()
executor = ThreadPoolExecutor()


@router.post("/move")
async def move(params: MovementParams):
    try:
        await asyncio.get_event_loop().run_in_executor(
            executor, lambda: global_state.stage.move(params.x, params.y)
        )
        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/move_and_log")
async def move_and_log(params: MoveAndLogParams):
    try:
        await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: global_state.stage.move_and_log(
                params.x, params.y, params.x_step_size, params.sample_rate
            ),
        )
        return {"status": "success", "message": "Movement and logging completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/start")
async def start_movement(params: RectangleParams):
    try:
        future = asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: global_state.stage.move_in_rectangle(
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
                except Exception as e:
                    print(f"Error closing {ws} websocket: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/home")
async def home(params: ChannelParams):
    try:
        if params.channel_direction == "x":
            await asyncio.get_event_loop().run_in_executor(
                executor, lambda: global_state.stage.home_channel(1)
            )
        elif params.channel_direction == "y":
            await asyncio.get_event_loop().run_in_executor(
                executor, lambda: global_state.stage.home_channel(2)
            )
        else:
            await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: (
                    global_state.stage.home_channel(1),
                    global_state.stage.home_channel(2),
                ),
            )
        return {"status": "success", "message": "Homing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/get_movement_params")
async def get_movement_params_api():
    try:
        params = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: (
                global_state.stage.get_movement_params(1),
                global_state.stage.get_movement_params(2),
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
    try:
        await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: (
                global_state.stage.channel[1].SetHomingVelocity(
                    Decimal(params.channel1.homing_velocity)
                ),
                global_state.stage.channel[1].SetVelocityParams(
                    Decimal(params.channel1.max_velocity),
                    Decimal(params.channel1.acceleration),
                ),
                global_state.stage.channel[2].SetHomingVelocity(
                    Decimal(params.channel2.homing_velocity)
                ),
                global_state.stage.channel[2].SetVelocityParams(
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
    try:
        position = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: (
                global_state.stage.channel[1].DevicePosition,
                global_state.stage.channel[2].DevicePosition,
            ),
        )
        return {"status": "success", "x": f"{position[0]}", "y": f"{position[1]}"}
    except Exception as e:
        return {"status": "error", "x": "NaN", "y": "NaN"}


@router.get("/lockin/settings")
async def get_lockin_settings():
    try:
        settings = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: {
                "sensitivity": global_state.lockin.get_sensitivity(),
                "time_constant": global_state.lockin.get_time_constant(),
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
async def change_lockin_sensitivity(params: LockinSensitivityRequest):
    try:
        current_sensitivity = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: global_state.lockin.get_sensitivity()
        )
        new_sensitivity = current_sensitivity + (1 if params.increment else -1)
        if 0 <= new_sensitivity <= 27:
            await asyncio.get_event_loop().run_in_executor(
                executor, lambda: global_state.lockin.set_sensitivity(new_sensitivity)
            )
            return {"status": "success", "sensitivity": new_sensitivity}
        else:
            return {"status": "error", "message": "Sensitivity out of range"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/lockin/time_constant")
async def change_lockin_time_constant(params: LockinTimeConstantRequest):
    try:
        current_time_constant = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: global_state.lockin.get_time_constant()
        )
        new_time_constant = current_time_constant + (1 if params.increment else -1)
        if 0 <= new_time_constant <= 23:
            await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: global_state.lockin.set_time_constant(new_time_constant),
            )
            return {"status": "success", "time_constant": new_time_constant}
        else:
            return {"status": "error", "message": "Time constant out of range"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/multimeter/settings")
async def get_multimeter_settings():
    try:
        settings = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: {
                "aperture": global_state.multimeter.get_aperture(),
                "terminal": global_state.multimeter.get_terminal(),
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
    try:
        success = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: global_state.multimeter.set_aperture(params.nplc)
        )
        if success:
            return {"status": "success", "aperture": params.nplc}
        else:
            return {"status": "error", "message": "Failed to set aperture"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/multimeter/terminal")
async def set_multimeter_terminal(params: MultimeterTerminalRequest):
    try:
        success = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: global_state.multimeter.set_terminal(params.terminal)
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
        result = await analyze_fdpbd(validated_params.dict(), file)
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in params")
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid eta_down format: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def analyze_fdpbd(params: dict, file: UploadFile) -> FDPBDResult:
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
        params_dict = json.loads(params)
        if isinstance(params_dict.get("eta_down"), str):
            params_dict["eta_down"] = [
                float(x) for x in params_dict["eta_down"].split(",") if x.strip()
            ]
        validated_params = FDPBDParams(**params_dict)
        result = await analyze_fdpbd(validated_params.dict(), file)
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in params")
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid eta_down format: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in params")
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid parameter format: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def read_root():
    return {"status": "API is running"}
