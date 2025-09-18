from dataclasses import dataclass

from spells.spell_type import SpellType


@dataclass(frozen=True)
class DisplaySpellEntry:
    id: int
    type: SpellType
    dropdown_name: str  # eg "12 - alohomora"
