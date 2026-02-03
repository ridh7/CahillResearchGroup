class GlobalState:
    def __init__(self):
        self.stage = None
        self.lockin = None
        self.multimeter = None
        self.ws_lockin = None
        self.ws_multimeter = None
        self.ws_stage = None


global_state = GlobalState()
