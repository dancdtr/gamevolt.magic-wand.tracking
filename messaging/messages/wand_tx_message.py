from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class WandTxMessage(Message):
    tag_id: str
    enabled: bool
    sequence_id: int
