from fastapi import APIRouter
from app.models.rectangle import RectangleParams
from app.services.movement import move_in_rectangle, home_channel
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


@router.get("/home_x")
async def home_x():
    try:
        home_channel(global_state.channel1)
        return {"status": "success", "message": "Homing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/home_y")
async def home_y():
    try:
        home_channel(global_state.channel2)
        return {"status": "success", "message": "Homing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/")
def read_root():
    return {"status": "API is running"}
