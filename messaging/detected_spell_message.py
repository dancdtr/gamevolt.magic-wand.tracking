from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class DetectedSpellMessage(Message):
    WandId: str
    SpellName: str
    Accuracy: float
