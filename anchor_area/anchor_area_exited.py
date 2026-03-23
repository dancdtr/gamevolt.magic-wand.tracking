from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class AnchorAreaExitedMessage(Message):
    AreaId: str
    WandId: str
