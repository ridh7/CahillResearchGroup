from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.routers import endpoints
from contextlib import asynccontextmanager
from app.core.devices import *
from app.models.state import global_state
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    global_state.device = initialize_device("103387864")
    global_state.channel1, global_state.motor_config1 = initialize_channel(
        global_state.device, 1
    )
    global_state.channel2, global_state.motor_config2 = initialize_channel(
        global_state.device, 2
    )
    global_state.lockin = SR865A()
    global_state.multimeter = BKPrecision5493C()
    yield
    global_state.device.Disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)


@app.websocket("/ws/lockin")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            values = global_state.lockin.read_values()
            await websocket.send_json(values)
            await asyncio.sleep(0.1)  # 10Hz update rate
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
