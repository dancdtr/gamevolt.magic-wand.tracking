from dataclasses import dataclass


@dataclass(frozen=True)
class WandRotationRaw:
    id: str
    ms: int
    fx: float
    fy: float
    fz: float
