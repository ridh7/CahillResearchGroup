"""
Shared state manager for thread-safe instrument data caching.

Coordinates between WebSocket streaming threads and synchronous scan operations.
Prevents GPIB communication conflicts by caching latest values and using pause flags.
"""

import asyncio
import queue
import threading


class SharedState:
    """
    Thread-safe cache for latest instrument readings.

    Attributes:
        latest_lockin_values: Most recent X, Y, frequency from lock-in
        latest_multimeter_value: Most recent voltage reading
        latest_stage_values: Most recent X, Y position
        value_lock: Threading lock to prevent race conditions
        pause_lockin_reading: Event flag to pause lock-in queries during scans
            (prevents GPIB conflicts when stage scan needs exclusive access)
        pause_stage_reading: Event flag to pause stage position queries during scans
            (prevents VISA resource locking when scan thread needs exclusive device access)
    """

    def __init__(self):
        self.latest_lockin_values = None
        self.latest_multimeter_value = None
        self.latest_stage_values = None
        self.value_lock = threading.Lock()
        self.pause_lockin_reading = asyncio.Event()
        self.pause_stage_reading = asyncio.Event()
        self.pause_multimeter_reading = asyncio.Event()
        self.scan_data_queue = queue.Queue()
        self.scan_active = False


shared_state = SharedState()
