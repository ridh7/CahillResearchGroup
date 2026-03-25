import contextlib
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings as app_settings
from app.models.state import global_state
from app.routers import analysis, sse

logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent / "static"

# Detect hardware availability at import time
_hardware_available = True
try:
    from app.core.lockin import SR865A
    from app.core.multimeter import BKPrecision5493C
    from app.core.stage import ThorlabsBBD302
    from app.routers import lockin, multimeter, stage
except ImportError as e:
    _hardware_available = False
    logger.warning(
        "Hardware modules unavailable (%s) — running in analysis-only mode", e
    )


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Application lifespan manager for instrument initialization and cleanup.

    Startup: Initialize ThreadPoolExecutor and all instruments (stage, lock-in, multimeter).
    Order matters - stage initialization includes homing which takes ~10s.
    If hardware modules are not installed, starts in analysis-only mode.

    Shutdown: Disconnect hardware and shutdown executor.
    """
    global_state.executor = ThreadPoolExecutor()

    if _hardware_available:
        try:
            global_state.stage = ThorlabsBBD302()
            global_state.lockin = SR865A()
            global_state.multimeter = BKPrecision5493C()
            global_state.pause_lockin_reading.clear()
            global_state.pause_stage_reading.clear()
            global_state.pause_multimeter_reading.clear()
            logger.info("All hardware initialized successfully")
        except Exception as e:
            logger.warning(
                "Hardware initialization failed (%s) — analysis endpoints still available",
                e,
            )
    else:
        logger.info(
            "Running in analysis-only mode (no hardware dependencies installed)"
        )

    yield

    if global_state.stage is not None:
        with contextlib.suppress(Exception):
            global_state.stage.device.Disconnect()
    if global_state.executor is not None:
        global_state.executor.shutdown(wait=True)


app = FastAPI(lifespan=lifespan)

if app_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Always available
app.include_router(analysis.router, tags=["analysis"])
app.include_router(sse.router, tags=["sse"])

# Hardware-dependent routers
if _hardware_available:
    app.include_router(stage.router, tags=["stage"])
    app.include_router(lockin.router, tags=["lockin"])
    app.include_router(multimeter.router, tags=["multimeter"])

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
        # Next.js static export: /fdpbd -> fdpbd.html
        page_html = FRONTEND_DIR / f"{path}.html"
        if page_html.is_file():
            return FileResponse(str(page_html))
        # Subfolder style: /fdpbd -> fdpbd/index.html
        index_html = FRONTEND_DIR / path / "index.html"
        if index_html.is_file():
            return FileResponse(str(index_html))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
