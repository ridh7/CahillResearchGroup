from __future__ import annotations

import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.lockin import SR865A
    from app.core.multimeter import BKPrecision5493C
    from app.core.stage import ThorlabsBBD302


class GlobalState:
    """
    Unified application state for hardware devices and cached data.

    Hardware instances:
        stage, lockin, multimeter: Device driver instances

    Cached instrument data (thread-safe):
        latest_lockin_values: Most recent X, Y, frequency from lock-in
        latest_multimeter_value: Most recent voltage reading
        latest_stage_values: Most recent X, Y position
        value_lock: Threading lock to prevent race conditions

    Coordination flags:
        pause_lockin_reading: Event flag to pause lock-in queries during scans
            (prevents GPIB conflicts when stage scan needs exclusive access)
        pause_stage_reading: Event flag to pause stage position queries during scans
            (prevents VISA resource locking when scan thread needs exclusive device access)

    Thread pool:
        executor: ThreadPoolExecutor for running blocking hardware operations in background threads
    """

    def __init__(self) -> None:
        # Hardware devices
        self.stage: ThorlabsBBD302 | None = None
        self.lockin: SR865A | None = None
        self.multimeter: BKPrecision5493C | None = None

        # Thread pool for blocking operations
        self.executor: ThreadPoolExecutor | None = None

        # Cached instrument readings (thread-safe)
        self.latest_lockin_values = None
        self.latest_multimeter_value = None
        self.latest_stage_values = None
        self.value_lock = threading.Lock()

        # Synchronization flags
        self.pause_lockin_reading = threading.Event()
        self.pause_stage_reading = threading.Event()
        self.pause_multimeter_reading = threading.Event()

        # Scan coordination
        self.scan_data_queue: queue.Queue = queue.Queue()
        self.scan_active = False
        self.scan_generation = (
            0  # incremented each new scan; old threads abort on mismatch
        )


global_state = GlobalState()
