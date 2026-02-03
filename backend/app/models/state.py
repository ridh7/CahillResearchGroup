from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import WebSocket

    from app.core.lockin import SR865A
    from app.core.multimeter import BKPrecision5493C
    from app.core.stage import ThorlabsBBD302


class GlobalState:
    """Global state container for hardware devices and WebSocket connections."""

    def __init__(self) -> None:
        self.stage: ThorlabsBBD302 | None = None
        self.lockin: SR865A | None = None
        self.multimeter: BKPrecision5493C | None = None
        self.ws_lockin: WebSocket | None = None
        self.ws_multimeter: WebSocket | None = None
        self.ws_stage: WebSocket | None = None


global_state = GlobalState()
