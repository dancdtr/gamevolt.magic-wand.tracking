from __future__ import annotations

from dataclasses import dataclass

from motion.direction.direction_type import DirectionType


@dataclass(frozen=True)
class SpellStep:
    allowed: frozenset[DirectionType]
    min_duration_s: float = 0.0  # required dwell in this step
    required: bool = False
