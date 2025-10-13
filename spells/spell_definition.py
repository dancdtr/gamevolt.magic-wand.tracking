from dataclasses import dataclass
from typing import Sequence

from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


@dataclass(frozen=True)
class SpellDefinition:
    id: str
    name: str
    step_groups: Sequence[SpellStepGroup]

    min_spell_steps: int  # minimum matched spell steps for completion
    max_total_duration_s: float | None = None  # optional time window for whole spell
    max_idle_gap_s: float = 0.20  # how much NONE can tolerated between steps

    @property
    def steps(self) -> list[SpellStep]:
        steps = []
        for group in self.step_groups:
            steps += group.steps
        return steps

    @property
    def reversed_steps(self) -> list[SpellStep]:
        return list(reversed(self.steps))
