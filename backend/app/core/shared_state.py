import threading
import asyncio


class SharedState:
    def __init__(self):
        self.latest_lockin_values = None
        self.latest_multimeter_value = None
        self.latest_stage_values = None
        self.value_lock = threading.Lock()
        self.pause_lockin_reading = asyncio.Event()


shared_state = SharedState()
