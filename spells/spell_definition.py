from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


@dataclass
class SpellDefinition:
    id: str
    name: str
    step_groups: Sequence[SpellStepGroup]

    # Minimum matched steps (required+optional) for a spell to count
    min_spell_steps: int

    # Rule toggles
    check_duration: bool = True
    check_distance: bool = True
    check_group_distance_ratio: bool = False
    check_group_duration_ratio: bool = False  # reserved for later

    # Duration / distance constraints
    min_total_duration_s: float | None = None
    max_total_duration_s: float | None = None
    min_total_distance: float | None = None
    max_total_distance: float | None = None

    # Group ratio tuning
    group_distance_rel_tol: float = 0.25
    group_distance_min_total: float = 1e-6
    group_duration_rel_tol: float = 0.25
    group_duration_min_total_s: float = 1e-3

    # Per-segment NONE tolerance
    max_idle_gap_s: float = 0.20

    # How much total "filler" time (any direction, incl NONE)
    # can appear between key steps before we reject the match.
    max_filler_duration_s: float = 0.25

    # Minimum "rest" time before the spell starts, or None to disable.
    min_pre_pause_s: float | None = None
    # Minimum "rest" time after the spell ends, or None to disable.
    min_post_pause_s: float | None = None
    # Threshold below which mean_speed counts as "paused".
    pause_speed_threshold: float = 0.01

    @property
    def steps(self) -> list[SpellStep]:
        steps: list[SpellStep] = []
        for group in self.step_groups:
            steps += group.steps
        return steps

    @property
    def reversed_steps(self) -> list[SpellStep]:
        return list(reversed(self.steps))
