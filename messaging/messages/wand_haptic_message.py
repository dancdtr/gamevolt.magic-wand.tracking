from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class WandHapticMessage(Message):
    tag_id: str
    pattern_id: int
