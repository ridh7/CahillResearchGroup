from fastapi import WebSocket


class GlobalState:
    def __init__(self):
        self.stage = None
        self.lockin = None
        self.multimeter = None
        self.ws_lockin: WebSocket = None
        self.ws_multimeter: WebSocket = None
        self.ws_stage: WebSocket = None


global_state = GlobalState()
