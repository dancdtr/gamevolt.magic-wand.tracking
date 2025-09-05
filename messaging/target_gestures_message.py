from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class TargetGesturesMessage(Message):
    GestureNames: list[str]
