import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.lockin import SR865A
from app.core.multimeter import BKPrecision5493C
from app.core.stage import ThorlabsBBD302
from app.models.state import global_state
from app.routers import analysis, lockin, multimeter, stage, websockets

FRONTEND_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Application lifespan manager for instrument initialization and cleanup.

    Startup: Initialize ThreadPoolExecutor and all instruments (stage, lock-in, multimeter).
    Order matters - stage initialization includes homing which takes ~10s.

    Shutdown: Close WebSocket connections, disconnect hardware, and shutdown executor.
    """
    global_state.executor = ThreadPoolExecutor()
    global_state.stage = ThorlabsBBD302()
    global_state.lockin = SR865A()
    global_state.multimeter = BKPrecision5493C()
    global_state.pause_lockin_reading.clear()
    global_state.pause_stage_reading.clear()
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
    if global_state.executor is not None:
        global_state.executor.shutdown(wait=True)


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

app.include_router(stage.router, tags=["stage"])
app.include_router(lockin.router, tags=["lockin"])
app.include_router(multimeter.router, tags=["multimeter"])
app.include_router(analysis.router, tags=["analysis"])
app.include_router(websockets.router, tags=["websockets"])

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
