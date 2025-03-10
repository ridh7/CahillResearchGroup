from fastapi import APIRouter
from concurrent.futures import ThreadPoolExecutor
import asyncio
from app.models.stage import *
from app.models.channel import *
from app.models.state import global_state
import clr
from System import Decimal

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


@router.post("/start")
async def start_movement(params: RectangleParams):
    try:
        await asyncio.get_event_loop().run_in_executor(
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

        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
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


@router.get("/")
def read_root():
    return {"status": "API is running"}
