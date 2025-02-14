from pydantic import BaseModel


class ChannelParams(BaseModel):
    channel_direction: str
    
class ChannelSettings(BaseModel):
    homing_velocity: float
    max_velocity: float
    acceleration: float

class Settings(BaseModel):
    channel1: ChannelSettings
    channel2: ChannelSettings
