"""SSE endpoints for real-time hardware data streaming."""

import asyncio
import json
import queue

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.models.state import global_state

router = APIRouter()

# Cancellation tokens for single-connection enforcement per device stream.
# When a new SSE connection arrives, the old token is set (signaling the
# previous generator to exit), then a fresh token is created.
_lockin_cancel: asyncio.Event | None = None
_multimeter_cancel: asyncio.Event | None = None
_stage_cancel: asyncio.Event | None = None

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


async def _lockin_generator(request: Request, cancel: asyncio.Event):
    """Stream lock-in amplifier data (X, Y, frequency) at ~200Hz."""
    if global_state.lockin is None:
        yield f"data: {json.dumps({'error': 'Lock-in amplifier not initialized'})}\n\n"
        return
    lockin = global_state.lockin
    while not cancel.is_set():
        if await request.is_disconnected():
            break
        if global_state.pause_lockin_reading.is_set():
            await asyncio.sleep(0.02)
            continue
        values = lockin.read_values()
        with global_state.value_lock:
            global_state.latest_lockin_values = values
        yield f"data: {json.dumps(values)}\n\n"
        await asyncio.sleep(0.005)


async def _multimeter_generator(request: Request, cancel: asyncio.Event):
    """Stream multimeter voltage readings at ~200Hz."""
    if global_state.multimeter is None:
        yield f"data: {json.dumps({'error': 'Multimeter not initialized'})}\n\n"
        return
    multimeter = global_state.multimeter
    while not cancel.is_set():
        if await request.is_disconnected():
            break
        if global_state.pause_multimeter_reading.is_set():
            await asyncio.sleep(0.02)
            continue
        value = multimeter.read_value()
        with global_state.value_lock:
            global_state.latest_multimeter_value = value
        yield f"data: {json.dumps({'value': value})}\n\n"
        await asyncio.sleep(0.005)


async def _stage_generator(request: Request, cancel: asyncio.Event):
    """Stream motorized stage position (X, Y) at ~200Hz."""
    if global_state.stage is None:
        yield f"data: {json.dumps({'error': 'Stage not initialized'})}\n\n"
        return
    stage = global_state.stage
    while not cancel.is_set():
        if await request.is_disconnected():
            break
        if global_state.pause_stage_reading.is_set():
            await asyncio.sleep(0.02)
            continue
        values = stage.read_values()
        with global_state.value_lock:
            global_state.latest_stage_values = values
        yield f"data: {json.dumps(values)}\n\n"
        await asyncio.sleep(0.005)


async def _scan_data_generator(request: Request):
    """Stream scan measurement points from the queue.

    Waits up to 5s for scan_active, then forwards each point from
    scan_data_queue. Sends {"type": "scan_complete"} when done.
    """
    for _ in range(500):
        if global_state.scan_active:
            break
        if await request.is_disconnected():
            return
        await asyncio.sleep(0.01)

    if not global_state.scan_active:
        yield f"data: {json.dumps({'type': 'scan_complete'})}\n\n"
        return

    while True:
        if await request.is_disconnected():
            return
        try:
            point = global_state.scan_data_queue.get_nowait()
            yield f"data: {json.dumps(point)}\n\n"
        except queue.Empty:
            if not global_state.scan_active:
                yield f"data: {json.dumps({'type': 'scan_complete'})}\n\n"
                return
            await asyncio.sleep(0.01)


@router.get("/sse/lockin")
async def sse_lockin(request: Request):
    """SSE endpoint for lock-in amplifier real-time data streaming."""
    global _lockin_cancel  # noqa: PLW0603
    if _lockin_cancel is not None:
        _lockin_cancel.set()
    _lockin_cancel = asyncio.Event()
    return StreamingResponse(
        _lockin_generator(request, _lockin_cancel),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/sse/multimeter")
async def sse_multimeter(request: Request):
    """SSE endpoint for multimeter real-time voltage streaming."""
    global _multimeter_cancel  # noqa: PLW0603
    if _multimeter_cancel is not None:
        _multimeter_cancel.set()
    _multimeter_cancel = asyncio.Event()
    return StreamingResponse(
        _multimeter_generator(request, _multimeter_cancel),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/sse/stage")
async def sse_stage(request: Request):
    """SSE endpoint for motorized stage position streaming."""
    global _stage_cancel  # noqa: PLW0603
    if _stage_cancel is not None:
        _stage_cancel.set()
    _stage_cancel = asyncio.Event()
    return StreamingResponse(
        _stage_generator(request, _stage_cancel),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/sse/scan_data")
async def sse_scan_data(request: Request):
    """SSE endpoint for live scan data points during acquisition."""
    return StreamingResponse(
        _scan_data_generator(request),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
