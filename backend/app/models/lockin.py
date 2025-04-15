from pydantic import BaseModel


class LockinSensitivityRequest(BaseModel):
    increment: bool


class LockinTimeConstantRequest(BaseModel):
    increment: bool
