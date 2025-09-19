from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class DetectedGesturesMessage(Message):
    id: str
    duration: float
    names: list[str]
