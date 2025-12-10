from dataclasses import dataclass


@dataclass
class WandRotationRaw:
    id: str  # tag hex, e.g. "E001"
    yaw: float  # degrees
    pitch: float  # degrees
    ms: int  # synthesized per-sample timestamp (ms)
