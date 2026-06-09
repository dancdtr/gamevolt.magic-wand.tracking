from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class AnchorAreaEnteredMessage(Message):
    AreaId: str
    WandId: str
