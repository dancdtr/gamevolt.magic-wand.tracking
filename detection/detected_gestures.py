from dataclasses import dataclass

from classification.gesture_type import GestureType

# from detection.detected_gesture import DetectedGesture


@dataclass(frozen=True)
class DetectedGestures:
    duration: float
    types: list[GestureType]
    # wand_id: str
    # duration_ms: int or start/end ts
    # gesture_id: int
    # confidence: float

    # TODO temp helper until can display multiple gestures at the same time
    @property
    def main_gesture(self) -> GestureType:
        return self.types[0] if self.types else GestureType.NONE
