"""WebSocket endpoints for real-time hardware data streaming."""

import asyncio
from contextlib import suppress

from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect

from app.models.state import global_state

router = APIRouter()


async def send_lockin_data(websocket: WebSocket):
    """
    Stream lock-in amplifier data to frontend at ~200Hz (5ms interval).

    Uses pause mechanism to prevent reading during stage scan operations,
    as simultaneous GPIB queries can cause device communication conflicts.
    Cached values in global_state allow other operations to access latest
    data without blocking WebSocket stream.
    """
    if global_state.lockin is None:
        await websocket.close(code=1003, reason="Lock-in amplifier not initialized")
        return
    lockin = global_state.lockin  # Capture reference for type narrowing
    while True:
        if global_state.pause_lockin_reading.is_set():
            await asyncio.sleep(0.02)
            continue
        values = lockin.read_values()
        with global_state.value_lock:
            global_state.latest_lockin_values = values
        await websocket.send_json(values)
        await asyncio.sleep(0.005)


async def send_multimeter_data(websocket: WebSocket):
    """
    Stream multimeter voltage readings to frontend at ~200Hz (5ms interval).

    Caches latest value in global_state for synchronous access during
    stage scans, ensuring voltage measurements align with position data.
    """
    if global_state.multimeter is None:
        await websocket.close(code=1003, reason="Multimeter not initialized")
        return
    multimeter = global_state.multimeter  # Capture reference for type narrowing
    while True:
        value = multimeter.read_value()
        with global_state.value_lock:
            global_state.latest_multimeter_value = value
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
        if global_state.pause_stage_reading.is_set():
            await asyncio.sleep(0.02)
            continue
        values = stage.read_values()
        with global_state.value_lock:
            global_state.latest_stage_values = values
        await websocket.send_json(values)
        await asyncio.sleep(0.005)


@router.websocket("/ws/lockin")
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


@router.websocket("/ws/multimeter")
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


@router.websocket("/ws/stage")
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
