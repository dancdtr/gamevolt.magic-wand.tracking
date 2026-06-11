"""Tunables for the $1 cast scorer: gates (boolean vetoes), bonus weights, quality tiers.

Spike-stage defaults live here as code so they're easy to tweak while calibrating.
Move to appsettings.yml once the values settle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from spells.spell_cast_quality import SpellCastQuality


@dataclass(frozen=True)
class GateSettings:
    # Below this $1 match accuracy (0..1) the shape isn't this spell at all.
    min_match_accuracy: float = 0.50
    # Reject accidental flicks / dawdles.
    min_duration_s: float = 0.30
    max_duration_s: float = 4.0
    # Absolute path length floor. $1 is scale-blind, so this is the only size check.
    # 0.0 = disabled until calibrated against real logged path values.
    min_path_length: float = 0.0


@dataclass(frozen=True)
class BonusSettings:
    # XP: points per unique spell already cast by the player, and the cap.
    xp_per_unique_spell: float = 0.5
    xp_max: float = 19.0  # 38 spells * 0.5

    # Cadence: rewards even (low-variance) speed across the stroke.
    cadence_max: float = 10.0

    # Tempo: full bonus inside the ideal duration band, linear decay outside.
    tempo_max: float = 5.0
    tempo_ideal_min_s: float = 0.6
    tempo_ideal_max_s: float = 2.5
    tempo_decay_s: float = 1.5  # span over which the bonus falls to zero past the band

    # Pity / struggle bonus: points per prior consecutive failed attempt. Only ever applied
    # to a gate-passing cast that fell short of the lowest tier, and capped at that tier.
    streak_per_fail: float = 5.0


@dataclass(frozen=True)
class ScoringSettings:
    gates: GateSettings = field(default_factory=GateSettings)
    bonuses: BonusSettings = field(default_factory=BonusSettings)

    # Total-score thresholds → quality tier. Below the lowest = not recognized.
    quality_thresholds: dict[SpellCastQuality, int] = field(
        default_factory=lambda: {
            SpellCastQuality.RUDIMENTARY: 60,
            SpellCastQuality.SKILLED: 75,
            SpellCastQuality.EXPERIENCED: 95,
            SpellCastQuality.MASTERED: 115,
        }
    )
