from dataclasses import dataclass

from spells.spell_step import SpellStep


@dataclass(frozen=True)
class SpellStepGroup:
    name: str
    steps: list[SpellStep]
    # relative_duration: float
    relative_distance: float
