from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class ZoneExitedMessage(Message):
    ZoneId: str
    WandId: str
