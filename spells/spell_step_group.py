from dataclasses import dataclass

from spells.spell_step import SpellStep


@dataclass(frozen=True)
class SpellStepGroup:
    name: str
    steps: list[SpellStep]
    min_steps: int = 0
