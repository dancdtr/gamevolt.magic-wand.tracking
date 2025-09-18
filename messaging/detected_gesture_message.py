from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class DetectedGesturesMessage(Message):
    duration: float
    names: list[str]
    # id: int = 0  # id of the gesture
