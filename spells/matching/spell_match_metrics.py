from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class SpellMatchMetrics:
    total_duration_s: float
    filler_duration_s: float
    total_distance: float

    group_distance: Sequence[float]
    group_duration_s: Sequence[float]

    used_steps: int
    total_steps: int

    required_matched: int
    required_total: int
    optional_matched: int
    optional_total: int
