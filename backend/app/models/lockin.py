from pydantic import BaseModel


class LockinSensitivityRequest(BaseModel):
    increment: bool


class LockinTimeConstantRequest(BaseModel):
    increment: bool


class LockinFrequencyRequest(BaseModel):
    frequency: float


class LockinFilterSlopeRequest(BaseModel):
    code: int
