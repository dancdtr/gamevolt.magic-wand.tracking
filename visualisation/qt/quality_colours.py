from __future__ import annotations

from spells.scoring.cast_score import CastScore
from spells.spell_cast_quality import SpellCastQuality

QUALITY_COLOURS: dict[SpellCastQuality, str] = {
    SpellCastQuality.RUDIMENTARY: "#facc15",  # yellow
    SpellCastQuality.SKILLED: "#7dd3fc",  # light blue
    SpellCastQuality.EXPERIENCED: "#4ade80",  # green
    SpellCastQuality.MASTERED: "#c4b5fd",  # light purple
}
REJECT_COLOUR = "#ef4444"
NOISE_COLOUR = "#6b7280"  # grey: sub-threshold attempt (noise), not a real rejection


def colour_for_score(score: CastScore) -> str:
    """Quality tier colour for a cast; reject-red when gates failed or no tier awarded."""
    if not score.passed_gates or score.quality is None:
        return REJECT_COLOUR
    return QUALITY_COLOURS.get(score.quality, REJECT_COLOUR)
