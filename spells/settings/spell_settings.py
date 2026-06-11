"""Resolved per-spell scoring settings — the runtime shape the scorer consumes.

Built by `SpellScoringSettings.spell_settings(label)` from the appsettings `spell_scoring`
block (default + per-spell overrides). The code defaults below are the final fallback when
neither the override nor the `default` block specifies a field.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from spells.spell_cast_quality import SpellCastQuality


@dataclass(frozen=True)
class GateSettings:
    """Boolean vetoes (false-positive filter). A failed gate = cast rejected."""

    min_match_accuracy: float = 0.50
    min_duration_s: float = 0.30
    max_duration_s: float = 4.0
    min_path_length: float = 0.0  # 0 = disabled ($1 is scale-blind; calibrate per spell)


@dataclass(frozen=True)
class TempoSettings:
    """Ideal cast-duration band for the tempo bonus; full bonus inside, linear decay outside."""

    ideal_min_s: float = 0.6
    ideal_max_s: float = 2.5
    decay_s: float = 1.5


def _default_thresholds() -> dict[SpellCastQuality, int]:
    return {
        SpellCastQuality.RUDIMENTARY: 60,
        SpellCastQuality.SKILLED: 75,
        SpellCastQuality.EXPERIENCED: 95,
        SpellCastQuality.MASTERED: 115,
    }


@dataclass(frozen=True)
class SpellSettings:
    difficulty_weight: float = 1.0  # multiplies the base ($1 accuracy) score
    gates: GateSettings = field(default_factory=GateSettings)
    tempo: TempoSettings = field(default_factory=TempoSettings)
    quality_thresholds: dict[SpellCastQuality, int] = field(default_factory=_default_thresholds)

    @property
    def lowest_tier(self) -> tuple[SpellCastQuality, int]:
        """The lowest quality tier + its threshold — the ceiling the pity bonus can reach."""
        return min(self.quality_thresholds.items(), key=lambda kv: kv[1])
