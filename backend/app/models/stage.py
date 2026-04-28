from pydantic import BaseModel


class ScanParams(BaseModel):
    x1: float
    x2: float
    y1: float
    y2: float
    x_steps: int | None = None
    y_steps: int | None = None
    x_step_size: float | None = None
    y_step_size: float | None = None
    movement_mode: str = "stepSize"  # "steps" or "stepSize"
    motion_type: str = (
        "step_and_measure"  # "continuous" | "step_and_measure" | "hardware_triggered"
    )
    scan_pattern: str = "bidirectional"  # "bidirectional" or "unidirectional"
    record_retrace: bool = False  # for unidirectional: record backward sweep
    fast_axis: str = "y"  # "x" or "y"
    delay: float | None = None  # only used for step_and_measure
    sample_id: str = ""
    comments: str = ""
    save_dir: str = ""  # directory chosen by folder picker; empty = cwd


class MovementParams(BaseModel):
    x: float
    y: float


class PositionValidationParams(BaseModel):
    channel: int = 1  # 1=X, 2=Y
    start: float  # start position (mm)
    end: float  # end position (mm)
