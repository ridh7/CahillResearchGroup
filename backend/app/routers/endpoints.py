from fastapi import APIRouter
from app.models.rectangle import RectangleParams
from app.models.channel import *
from app.services.movement import *
from app.models.state import global_state

router = APIRouter()


@router.post("/start")
async def start_movement(params: RectangleParams):
    try:
        move_in_rectangle(
            params.x1,
            params.y1,
            params.x2,
            params.y2,
            params.steps,
            params.stepSize,
            global_state.channel1,
            global_state.channel2,
        )
        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/home")
async def home(params: ChannelParams):
    try:
        print(params.channel_direction)
        if params.channel_direction == "x":
            home_channel(global_state.channel1)
        elif params.channel_direction == "y":
            home_channel(global_state.channel2)
        else:
            home_channel(global_state.channel1)
            home_channel(global_state.channel2)
        return {"status": "success", "message": "Homing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/get_movement_params")
async def get_movement_params_api():
    try:
        home_params_x, vel_params_x = get_movement_params(global_state.channel1)
        home_params_y, vel_params_y = get_movement_params(global_state.channel2)
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
        global_state.channel1.SetHomingVelocity(Decimal(params.channel1.homing_velocity))
        global_state.channel1.SetVelocityParams(Decimal(params.channel1.max_velocity), Decimal(params.channel1.acceleration))
        global_state.channel2.SetHomingVelocity(Decimal(params.channel2.homing_velocity))
        global_state.channel2.SetVelocityParams(Decimal(params.channel2.max_velocity), Decimal(params.channel2.acceleration))
        return {
            "status": "success",
            "message": "movement params set"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/get_current_position")
async def get_current_position():
    try:
        x = global_state.channel1.DevicePosition
        y = global_state.channel2.DevicePosition
        return {
            "status": "success",
            "x": f"{x}",
            "y": f"{y}"
        }
    except Exception as e:
        return {"status": "error", "x": "NaN", "y": "NaN"}

@router.get("/")
def read_root():
    return {"status": "API is running"}
