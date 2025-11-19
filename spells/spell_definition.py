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

    min_spell_steps: int

    # ── Rule toggles ───────────────────────────────────────────────
    check_duration: bool = True
    check_distance: bool = True
    check_group_distance_ratio: bool = False

    # ── Duration constraints (for DurationRule) ───────────────────
    min_total_duration_s: float | None = None
    max_total_duration_s: float | None = None

    # ── Distance constraints (for DistanceRule) ───────────────────
    min_total_distance: float | None = None
    max_total_distance: float | None = None

    # ── Group distance ratio params (for GroupDistanceRatioRule) ──
    group_distance_rel_tol: float = 0.15  # how close to target ratio
    group_distance_min_total: float = 1e-6  # avoid div-by-zero

    # legacy per-segment idle tolerance for DirectionType.NONE
    max_idle_gap_s: float = 0.20

    # how much total "filler" time (any direction, incl NONE)
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
