from pydantic import BaseModel


class RectangleParams(BaseModel):
    x1: float
    x2: float
    y1: float
    y2: float
    x_steps: int
    y_steps: int
    x_step_size: float
    y_step_size: float
