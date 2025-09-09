from dataclasses import dataclass

from spell_type import SpellType


@dataclass(frozen=True)
class SpellEntry:
    id: int
    type: SpellType
    dropdown_name: str  # eg "12 - alohomora"
