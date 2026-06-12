from __future__ import annotations

from dataclasses import dataclass

from spells.matching.dollar_one.dollar_one_recognizer import Recognition
from spells.scoring.cast_score import CastScore

Point = tuple[float, float]


@dataclass(frozen=True)
class CastAttempt:
    """Every completed stroke that got scored — recognised or not.

    Unlike `SpellCast` (recognised casts only), this fires for *every* attempt so the
    visualiser can show rejected/low-quality casts and the full scoring breakdown.
    """

    wand_id: str
    score: CastScore
    candidates: tuple[Recognition, ...]  # top matches, best first

    stroke_points: tuple[Point, ...]  # raw stroke in wand space
    normalized_points: tuple[Point, ...]  # $1-prepared candidate (resampled + normalised)
    template_points: tuple[Point, ...]  # matched template, prepared; () if no template

    duration_s: float
    path_length: float
    point_count: int

    @property
    def template_label(self) -> str:
        return self.score.label
