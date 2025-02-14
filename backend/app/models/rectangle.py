from pydantic import BaseModel


class RectangleParams(BaseModel):
    x1: float
    x2: float
    y1: float
    y2: float
    steps: int
    stepSize: float
