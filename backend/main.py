from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.routers import endpoints
from contextlib import asynccontextmanager
from app.models.state import global_state
from app.core.stage import ThorlabsBBD302
from app.core.multimeter import BKPrecision5493C
from app.core.lockin import SR865A
import asyncio
from fastapi.websockets import WebSocketDisconnect
from app.core.shared_state import shared_state
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    global_state.stage = ThorlabsBBD302()
    global_state.lockin = SR865A()
    global_state.multimeter = BKPrecision5493C()
    shared_state.pause_lockin_reading.clear()
    yield
    for ws in [
        global_state.ws_lockin,
        global_state.ws_multimeter,
        global_state.ws_stage,
    ]:
        if ws is not None:
            try:
                await ws.close()
            except:
                pass
    global_state.stage.device.Disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)


async def send_lockin_data(websocket: WebSocket):
    while True:
        if shared_state.pause_lockin_reading.is_set():
            await asyncio.sleep(0.02)
            continue
        start_time = time.time()
        values = global_state.lockin.read_values()
        elapsed = time.time() - start_time
        with shared_state.value_lock:
            shared_state.latest_lockin_values = values
        await websocket.send_json(values)
        print(f"---Lock-in read time: {elapsed:.4f}s")
        await asyncio.sleep(0.005)


async def send_multimeter_data(websocket: WebSocket):
    while True:
        start_time = time.time()
        value = global_state.multimeter.read_value()
        elapsed = time.time() - start_time
        with shared_state.value_lock:
            shared_state.latest_multimeter_value = value
        await websocket.send_json({"value": value})
        print(f"---Multimeter read time: {elapsed:.4f}s")
        await asyncio.sleep(0.005)


async def send_stage_data(websocket: WebSocket):
    while True:
        start_time = time.time()
        values = global_state.stage.read_values()
        elapsed = time.time() - start_time
        with shared_state.value_lock:
            shared_state.latest_stage_values = values
        await websocket.send_json(values)
        print(f"---Stage read time: {elapsed:.4f}s")
        await asyncio.sleep(0.005)


@app.websocket("/ws/lockin")
async def websocket_endpoint(websocket: WebSocket):
    if global_state.ws_lockin is not None:
        try:
            await global_state.ws_lockin.close()
        except:
            pass
    await websocket.accept()
    global_state.ws_lockin = websocket
    task = asyncio.create_task(send_lockin_data(websocket))
    try:
        await task
    except WebSocketDisconnect:
        task.cancel()
    except Exception as e:
        print(f"Lockin websocket error: {e}")
        task.cancel()
        if global_state.ws_lockin == websocket:
            global_state.ws_lockin = None
        try:
            await websocket.close()
        except:
            pass


@app.websocket("/ws/multimeter")
async def websocket_multimeter_endpoint(websocket: WebSocket):
    if global_state.ws_multimeter is not None:
        try:
            await global_state.ws_multimeter.close()
        except:
            pass
    await websocket.accept()
    global_state.ws_multimeter = websocket
    task = asyncio.create_task(send_multimeter_data(websocket))
    try:
        await task
    except WebSocketDisconnect:
        task.cancel()
    except Exception as e:
        print(f"Multimeter websocket error: {e}")
        task.cancel()
        if global_state.ws_multimeter == websocket:
            global_state.ws_multimeter = None
        try:
            await websocket.close()
        except:
            pass


@app.websocket("/ws/stage")
async def websocket_stage_endpoint(websocket: WebSocket):
    if global_state.ws_stage is not None:
        try:
            await global_state.ws_stage.close()
        except:
            pass
    await websocket.accept()
    global_state.ws_stage = websocket
    task = asyncio.create_task(send_stage_data(websocket))
    try:
        await task
    except WebSocketDisconnect:
        task.cancel()
    except Exception as e:
        print(f"Stage websocket error: {e}")
        task.cancel()
        if global_state.ws_stage == websocket:
            global_state.ws_stage = None
        try:
            await websocket.close()
        except:
            pass
