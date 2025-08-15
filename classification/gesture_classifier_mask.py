from dataclasses import dataclass

from classification.gesture_type import GestureType


@dataclass
class GestureClassifierMask:
    target_gesture_types: list[GestureType]
