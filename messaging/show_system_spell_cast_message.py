from dataclasses import dataclass

from gamevolt.messaging.message import Message
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_type import SpellType
from wizards.hogwarts_house import HogwartsHouse


@dataclass
class ShowSystemSpellCastMessage(Message):
    spell_type: SpellType
    quality: SpellCastQuality
    house: HogwartsHouse
