"""
FastAPI dependency injection for hardware resources.

Each dependency function checks if the hardware is initialized in global_state
and raises HTTPException(503) if not available. This eliminates repeated
None-checking boilerplate across all endpoints.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from fastapi import HTTPException

from app.models.state import global_state

if TYPE_CHECKING:
    from app.core.lockin import SR865A
    from app.core.multimeter import BKPrecision5493C
    from app.core.stage import ThorlabsBBD302


def get_stage() -> "ThorlabsBBD302":
    """
    Dependency: Require stage to be initialized.

    Returns:
        ThorlabsBBD302: The motorized stage instance

    Raises:
        HTTPException: 503 Service Unavailable if stage is not initialized
    """
    if global_state.stage is None:
        raise HTTPException(status_code=503, detail="Stage not initialized")
    return global_state.stage


def get_stage_optional() -> "ThorlabsBBD302 | None":
    """
    Dependency: Optionally get stage (returns None if unavailable).

    Used by endpoints that need to handle stage absence gracefully
    without raising an exception (e.g., /get_current_position which
    returns {"x": "NaN", "y": "NaN"} instead of 503).

    Returns:
        ThorlabsBBD302 | None: Stage instance or None
    """
    return global_state.stage


def get_lockin() -> "SR865A":
    """
    Dependency: Require lock-in amplifier to be initialized.

    Returns:
        SR865A: The lock-in amplifier instance

    Raises:
        HTTPException: 503 Service Unavailable if lock-in is not initialized
    """
    if global_state.lockin is None:
        raise HTTPException(status_code=503, detail="Lock-in amplifier not initialized")
    return global_state.lockin


def get_multimeter() -> "BKPrecision5493C":
    """
    Dependency: Require multimeter to be initialized.

    Returns:
        BKPrecision5493C: The multimeter instance

    Raises:
        HTTPException: 503 Service Unavailable if multimeter is not initialized
    """
    if global_state.multimeter is None:
        raise HTTPException(status_code=503, detail="Multimeter not initialized")
    return global_state.multimeter


def get_executor() -> ThreadPoolExecutor:
    """
    Dependency: Get the thread pool executor for blocking operations.

    The executor is initialized in the app lifespan and should always
    be available during normal operation. This dependency provides type
    safety and defensive error handling.

    Returns:
        ThreadPoolExecutor: The shared executor instance

    Raises:
        HTTPException: 503 Service Unavailable if executor is not initialized
    """
    if global_state.executor is None:
        raise HTTPException(status_code=503, detail="Executor not initialized")
    return global_state.executor
