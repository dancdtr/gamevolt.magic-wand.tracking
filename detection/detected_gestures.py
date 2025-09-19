from dataclasses import dataclass

from classification.gesture_type import GestureType


@dataclass(frozen=True)
class DetectedGestures:
    gesture_id: str
    duration: float
    types: list[GestureType]
    # wand_id: str
    # duration_ms: int or start/end ts
    # confidence: float

    # TODO temp helper until can display multiple gestures at the same time
    @property
    def main_gesture(self) -> GestureType:
        return self.types[0] if self.types else GestureType.UNKNOWN
