import threading
import asyncio

latest_lockin_values = None
value_lock = threading.Lock()
pause_lockin_reading = asyncio.Event()
