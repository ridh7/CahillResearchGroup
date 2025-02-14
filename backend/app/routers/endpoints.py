from fastapi import APIRouter
from app.models.rectangle import RectangleParams
from app.models.channel import ChannelParams
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
            global_state.channel1,
            global_state.channel2,
        )
        return {"status": "success", "message": "Movement completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/home")
async def home(params: ChannelParams):
    try:
        if ChannelParams.channel_direction == "x":
            home_channel(global_state.channel1)
        elif ChannelParams.channel_direction == "y":
            home_channel(global_state.channel2)
        else:
            home_channel(global_state.channel1)
            home_channel(global_state.channel2)
        return {"status": "success", "message": "Homing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/get_movement_params")
async def get_movement_params_api():
    try:
        home_params_x, vel_params_x = get_movement_params(global_state.channel1)
        home_params_y, vel_params_y = get_movement_params(global_state.channel2)
        return {
            "status": "success",
            "homing_velocity_x": {home_params_x.Velocity},
            "max_velocity_x": {vel_params_x.MaxVelocity},
            "acceleration_x": {vel_params_x.Acceleration},
            "homing_velocity_y": {home_params_y.Velocity},
            "max_velocity_y": {vel_params_y.MaxVelocity},
            "acceleration_y": {vel_params_y.Acceleration},
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/")
def read_root():
    return {"status": "API is running"}
