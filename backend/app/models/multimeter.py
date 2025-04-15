from pydantic import BaseModel


class MultimeterApertureRequest(BaseModel):
    nplc: float


class MultimeterTerminalRequest(BaseModel):
    terminal: str
