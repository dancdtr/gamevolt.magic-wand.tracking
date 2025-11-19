from dataclasses import dataclass
from typing import Sequence

from gamevolt.configuration.settings_base import SettingsBase
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


@dataclass
class SpellDefinition:
    id: str
    name: str
    step_groups: Sequence[SpellStepGroup]

    # minimum matched spell steps for completion
    min_spell_steps: int

    min_total_duration: float | None = None
    max_total_duration: float | None = None

    # legacy per-segment idle tolerance for DirectionType.NONE
    max_idle_gap_s: float = 0.20

    # How much total "filler" time (any direction, incl NONE) can appear between key steps before we reject the match
    max_filler_duration_s: float = 0.25

    @property
    def steps(self) -> list[SpellStep]:
        steps: list[SpellStep] = []
        for group in self.step_groups:
            steps += group.steps
        return steps

    @property
    def reversed_steps(self) -> list[SpellStep]:
        return list(reversed(self.steps))
