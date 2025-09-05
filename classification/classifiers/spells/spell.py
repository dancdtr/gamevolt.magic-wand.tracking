from dataclasses import dataclass

from classification.gesture_type import GestureType
from spell_type import SpellType


@dataclass(frozen=True)
class Spell:
    type: SpellType
    definition: list[GestureType]

    def get_gestures(self) -> list[GestureType]:
        return list(set(self.definition))

    @property
    def length(self) -> int:
        return len(self.definition)

    @property
    def name(self) -> str:
        return self.type.name.lower()
