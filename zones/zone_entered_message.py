from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class ZoneEnteredMessage(Message):
    ZoneId: str
    WandId: str
