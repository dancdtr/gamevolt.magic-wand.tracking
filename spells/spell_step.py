from __future__ import annotations

from dataclasses import dataclass

from motion.direction.direction_type import DirectionType


@dataclass(frozen=True)
class SpellStep:
    allowed: frozenset[DirectionType]
    min_duration_s: float = 0.0  # required dwell in this step
    max_duration_s: float | None = None  # NEW
    required: bool = False

    @property
    def is_pause(self) -> bool:
        return self.allowed == frozenset({DirectionType.PAUSE})

    @property
    def is_scorable(self) -> bool:
        return not self.is_pause
