class GlobalState:
    def __init__(self):
        self.device = None
        self.channel1 = None
        self.channel2 = None
        self.motor_config1 = None
        self.motor_config2 = None
        self.lockin = None
        self.multimeter = None
        
global_state = GlobalState()