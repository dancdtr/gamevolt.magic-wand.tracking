from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class SpellMatchMetrics:
    total_duration_s: float

    # "True filler" only (NOT absorbed jitter)
    filler_duration_s: float

    # Scorable movement only (matched non-pause steps)
    scorable_duration_s: float
    total_distance: float  # keep as scorable distance (what you already do today)

    # Absorbed jitter (counts toward effective duration/distance + group ratios)
    absorbed_duration_s: float
    absorbed_distance: float

    group_distance: Sequence[float]  # scorable distance per group
    group_duration_s: Sequence[float]  # scorable duration per group
    group_steps_matched: list[int]  # scorable matched steps per group

    group_absorbed_distance: Sequence[float]  # absorbed distance per group
    group_absorbed_duration_s: Sequence[float]  # absorbed duration per group

    used_steps: int
    total_steps: int

    required_matched: int
    required_total: int
    optional_matched: int
    optional_total: int
