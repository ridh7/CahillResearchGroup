from pydantic import BaseModel


class ChannelParams(BaseModel):
    channel_direction: str
