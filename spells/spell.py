from dataclasses import dataclass

from spells.spell_type import SpellType


@dataclass(frozen=True)
class Spell:
    id: int
    type: SpellType

    @property
    def name(self) -> str:
        return self.type.name.lower()

    @property
    def long_name(self) -> str:
        return f"ID: {self.id}:'{self.name}'"

    def __str__(self) -> str:
        return self.long_name
