import asyncio
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketDisconnect

from app.core.lockin import SR865A
from app.core.multimeter import BKPrecision5493C
from app.core.shared_state import shared_state
from app.core.stage import ThorlabsBBD302
from app.models.state import global_state
from app.routers import endpoints

FRONTEND_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Application lifespan manager for instrument initialization and cleanup.

    Startup: Initialize all instruments (stage, lock-in, multimeter) in sequence.
    Order matters - stage initialization includes homing which takes ~10s.

    Shutdown: Close all WebSocket connections and disconnect stage hardware.
    """
    global_state.stage = ThorlabsBBD302()
    global_state.lockin = SR865A()
    global_state.multimeter = BKPrecision5493C()
    shared_state.pause_lockin_reading.clear()
    shared_state.pause_stage_reading.clear()
    yield
    for ws in [
        global_state.ws_lockin,
        global_state.ws_multimeter,
        global_state.ws_stage,
    ]:
        if ws is not None:
            with suppress(Exception):
                await ws.close()
    global_state.stage.device.Disconnect()


app = FastAPI(lifespan=lifespan)

cors_origins = os.environ.get("CORS_ORIGINS", "").strip()
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(endpoints.router)

# Serve static frontend assets if the build output exists
if FRONTEND_DIR.is_dir():
    next_static = FRONTEND_DIR / "_next"
    if next_static.is_dir():
        app.mount("/_next", StaticFiles(directory=str(next_static)), name="next_static")

    @app.get("/{path:path}")
    async def serve_spa(path: str) -> FileResponse:
        """Serve the static frontend, with SPA fallback for client-side routes."""
        file_path = FRONTEND_DIR / path
        if file_path.is_file():
            return FileResponse(str(file_path))
        page_html = FRONTEND_DIR / path / "index.html"
        if page_html.is_file():
            return FileResponse(str(page_html))
        return FileResponse(str(FRONTEND_DIR / "index.html"))


async def send_lockin_data(websocket: WebSocket):
    """
    Stream lock-in amplifier data to frontend at ~200Hz (5ms interval).

    Uses pause mechanism to prevent reading during stage scan operations,
    as simultaneous GPIB queries can cause device communication conflicts.
    Cached values in shared_state allow other operations to access latest
    data without blocking WebSocket stream.
    """
    if global_state.lockin is None:
        await websocket.close(code=1003, reason="Lock-in amplifier not initialized")
        return
    lockin = global_state.lockin  # Capture reference for type narrowing
    while True:
        if shared_state.pause_lockin_reading.is_set():
            await asyncio.sleep(0.02)
            continue
        values = lockin.read_values()
        with shared_state.value_lock:
            shared_state.latest_lockin_values = values
        await websocket.send_json(values)
        await asyncio.sleep(0.005)


async def send_multimeter_data(websocket: WebSocket):
    """
    Stream multimeter voltage readings to frontend at ~200Hz (5ms interval).

    Caches latest value in shared_state for synchronous access during
    stage scans, ensuring voltage measurements align with position data.
    """
    if global_state.multimeter is None:
        await websocket.close(code=1003, reason="Multimeter not initialized")
        return
    multimeter = global_state.multimeter  # Capture reference for type narrowing
    while True:
        value = multimeter.read_value()
        with shared_state.value_lock:
            shared_state.latest_multimeter_value = value
        await websocket.send_json({"value": value})
        await asyncio.sleep(0.005)


async def send_stage_data(websocket: WebSocket):
    """
    Stream motorized stage position to frontend at ~200Hz (5ms interval).

    Position updates are polled from Thorlabs .NET SDK and cached for
    synchronous access during move operations and scan logging.

    Pauses during scans to prevent VISA resource locking conflicts when
    scan thread needs exclusive device access for high-frequency position reads.
    """
    if global_state.stage is None:
        await websocket.close(code=1003, reason="Stage not initialized")
        return
    stage = global_state.stage  # Capture reference for type narrowing
    while True:
        if shared_state.pause_stage_reading.is_set():
            await asyncio.sleep(0.02)
            continue
        values = stage.read_values()
        with shared_state.value_lock:
            shared_state.latest_stage_values = values
        await websocket.send_json(values)
        await asyncio.sleep(0.005)


@app.websocket("/ws/lockin")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for lock-in amplifier real-time data streaming.

    Lifecycle management:
    1. Close any existing connection (prevents duplicate streams when user
       rapidly reconnects)
    2. Accept new connection and store in global_state
    3. Start async task to stream data
    4. On disconnect/error: cancel task, cleanup global reference, close socket

    This pattern ensures only one active stream per instrument at a time.
    """
    if global_state.ws_lockin is not None:
        with suppress(Exception):
            await global_state.ws_lockin.close()
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
        with suppress(Exception):
            await websocket.close()


@app.websocket("/ws/multimeter")
async def websocket_multimeter_endpoint(websocket: WebSocket):
    """WebSocket endpoint for multimeter real-time voltage streaming.

    Uses same connection lifecycle pattern as lock-in endpoint to ensure
    single active stream, preventing measurement conflicts.
    """
    if global_state.ws_multimeter is not None:
        with suppress(Exception):
            await global_state.ws_multimeter.close()
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
        with suppress(Exception):
            await websocket.close()


@app.websocket("/ws/stage")
async def websocket_stage_endpoint(websocket: WebSocket):
    """WebSocket endpoint for motorized stage position streaming.

    Streams X/Y position updates to frontend for real-time position tracking
    during manual movements and automated scans.
    """
    if global_state.ws_stage is not None:
        with suppress(Exception):
            await global_state.ws_stage.close()
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
        with suppress(Exception):
            await websocket.close()
