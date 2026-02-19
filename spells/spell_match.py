from __future__ import annotations

from dataclasses import dataclass

from motion.direction.direction_type import DirectionType


@dataclass(frozen=True)
class SpellMatch:
    wand_id: str
    spell_id: str
    spell_name: str
    start_ts_ms: int
    end_ts_ms: int
    duration_s: float

    matched_directions: tuple[DirectionType, ...]

    # Total matched steps (required + optional)
    segments_used: int
    total_segments: int

    # Required / optional breakdown
    required_matched: int
    required_total: int
    optional_matched: int
    optional_total: int

    # Filler diagnostics (useful for scoring later)
    filler_duration_s: float

    accuracy_score: float

    @property
    def accuracy(self) -> float:
        if self.total_segments <= 0:
            return 0.0
        return self.segments_used / self.total_segments

    @property
    def required_accuracy(self) -> float:
        if self.required_total <= 0:
            return 1.0
        return self.required_matched / self.required_total

    @property
    def optional_accuracy(self) -> float:
        if self.optional_total <= 0:
            return 0.0
        return self.optional_matched / self.optional_total

    @property
    def matched_drection_names(self) -> tuple[str, ...]:
        return tuple(d.name for d in self.matched_directions)
