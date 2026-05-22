from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class SpellCastMessage(Message):
    WandId: str
    SpellType: str
    Confidence: float
    Colour: str
