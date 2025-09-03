from dataclasses import dataclass

from classification.gesture_type import GestureType


@dataclass(frozen=True)
class DetectedGesture:
    t_ms: int
    type: GestureType
    # gesture_id: int
    # confidence: float
