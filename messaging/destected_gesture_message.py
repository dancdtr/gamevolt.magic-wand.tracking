from dataclasses import dataclass

from classification.gesture_type import GestureType
from gamevolt.messaging.message import Message


@dataclass
class DetectedGestureMessage(Message):
    ts: int
    name: str
    id: int = 0  # id of the gesture
