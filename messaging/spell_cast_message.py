from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class SpellCastMessage(Message):
    SpellType: str
    Confidence: float
