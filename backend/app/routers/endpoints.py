from fastapi import APIRouter
from app.models.rectangle import RectangleParams
from app.models.channel import *
from app.models.state import global_state
import clr
from System import Decimal

router = APIRouter()


@router.post("/start")
async def start_movement(params: RectangleParams):
    try:
        global_state.stage.move_in_rectangle(
            params.x1,
            params.y1,
            params.x2,
            params.y2,
            params.x_steps,
            params.y_steps,
            params.x_step_size,
            params.y_step_size,
        )
        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/home")
async def home(params: ChannelParams):
    try:
        print(params.channel_direction)
        if params.channel_direction == "x":
            global_state.stage.home_channel(1)
        elif params.channel_direction == "y":
            global_state.stage.home_channel(2)
        else:
            global_state.stage.home_channel(1)
            global_state.stage.home_channel(2)
        return {"status": "success", "message": "Homing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/get_movement_params")
async def get_movement_params_api():
    try:
        home_params_x, vel_params_x = global_state.stage.get_movement_params(1)
        home_params_y, vel_params_y = global_state.stage.get_movement_params(2)
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
        global_state.stage.channel[1].SetHomingVelocity(
            Decimal(params.channel1.homing_velocity)
        )
        global_state.stage.channel[1].SetVelocityParams(
            Decimal(params.channel1.max_velocity), Decimal(params.channel1.acceleration)
        )
        global_state.stage.channel[2].SetHomingVelocity(
            Decimal(params.channel2.homing_velocity)
        )
        global_state.stage.channel[2].SetVelocityParams(
            Decimal(params.channel2.max_velocity), Decimal(params.channel2.acceleration)
        )
        return {"status": "success", "message": "movement params set"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/get_current_position")
async def get_current_position():
    try:
        x = global_state.stage.channel[1].DevicePosition
        y = global_state.stage.channel[2].DevicePosition
        return {"status": "success", "x": f"{x}", "y": f"{y}"}
    except Exception as e:
        return {"status": "error", "x": "NaN", "y": "NaN"}


@router.get("/")
def read_root():
    return {"status": "API is running"}
