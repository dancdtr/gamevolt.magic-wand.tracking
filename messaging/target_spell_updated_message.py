from dataclasses import dataclass

from gamevolt.messaging.message import Message
from spells.spell_type import SpellType


@dataclass
class TargetSpellUpdatedMessage(Message):
    SpellTypeName: str
