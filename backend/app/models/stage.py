from pydantic import BaseModel


class RectangleParams(BaseModel):
    x1: float
    x2: float
    y1: float
    y2: float
    x_steps: int | None = None
    y_steps: int | None = None
    x_step_size: float | None = None
    y_step_size: float | None = None
    movement_mode: str
    delay: float | None = None


class MovementParams(BaseModel):
    x: float
    y: float


class MoveAndLogParams(BaseModel):
    x: float
    y: float
    x_step_size: float
    sample_rate: float
