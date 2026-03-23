from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class WandHapticSequenceMessage(Message):
    tag_id: str
    pattern_ids: list[int]
