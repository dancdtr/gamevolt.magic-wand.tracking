from dataclasses import dataclass

from spells.spell_type import SpellType


@dataclass(frozen=True)
class Spell:
    id: int
    code: str
    type: SpellType

    @property
    def name(self) -> str:
        return self.type.name.lower()

    @property
    def long_name(self) -> str:
        return f"({self.code}) ID: {self.id} - '{self.name}'"

    def __str__(self) -> str:
        return self.long_name
