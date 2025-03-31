from pydantic import BaseModel
from typing import Optional


class RectangleParams(BaseModel):
    x1: float
    x2: float
    y1: float
    y2: float
    x_steps: Optional[int] = None
    y_steps: Optional[int] = None
    x_step_size: Optional[float] = None
    y_step_size: Optional[float] = None
    movement_mode: str
    delay: Optional[float] = None


class MovementParams(BaseModel):
    x: float
    y: float


class MoveAndLogParams(BaseModel):
    x: float
    y: float
    sample_rate: float
