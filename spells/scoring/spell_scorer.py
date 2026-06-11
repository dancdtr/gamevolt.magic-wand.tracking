"""Turns a $1 match + stroke metrics + player XP into a total score and quality tier.

Pipeline: gates (boolean veto) -> base + bonuses -> total -> quality tier.
Decoupled from the legacy SpellDefinition / step-group scorer.
"""

from __future__ import annotations

import math

from motion.stroke.stroke_windower import Stroke
from spells.scoring.cast_score import CastScore
from spells.scoring.scoring_settings import ScoringSettings
from spells.scoring.streak_tracker import StreakTracker
from spells.scoring.xp_provider import XpProvider
from spells.spell_cast_quality import SpellCastQuality


class SpellScorer:
    def __init__(self, settings: ScoringSettings, xp_provider: XpProvider, streak_tracker: StreakTracker) -> None:
        self._settings = settings
        self._xp = xp_provider
        self._streak = streak_tracker

        # Lowest tier + its threshold = the ceiling the pity bonus can lift a cast to.
        self._lowest_tier, self._lowest_threshold = min(
            settings.quality_thresholds.items(), key=lambda kv: kv[1]
        )

    def score(self, player_id: str, label: str, match_accuracy: float, stroke: Stroke) -> CastScore:
        gates = self._settings.gates
        bonuses = self._settings.bonuses

        # ── Gates ─────────────────────────────────────────────
        failures: list[str] = []
        if match_accuracy < gates.min_match_accuracy:
            failures.append(f"accuracy<{gates.min_match_accuracy:.2f}")
        if stroke.duration_s < gates.min_duration_s:
            failures.append(f"duration<{gates.min_duration_s:.2f}s")
        if stroke.duration_s > gates.max_duration_s:
            failures.append(f"duration>{gates.max_duration_s:.2f}s")
        if gates.min_path_length > 0.0 and stroke.path_length < gates.min_path_length:
            failures.append(f"path<{gates.min_path_length:.2f}")

        if failures:
            return CastScore(
                label=label,
                match_accuracy=match_accuracy,
                base=0.0,
                xp_bonus=0.0,
                cadence_bonus=0.0,
                tempo_bonus=0.0,
                streak_bonus=0.0,
                difficulty_weight=1.0,
                total=0.0,
                quality=None,
                passed_gates=False,
                gate_failures=tuple(failures),
            )

        # ── Components ────────────────────────────────────────
        difficulty = 1.0  # per-spell weight; sourced per-template later
        base = match_accuracy * 100.0 * difficulty

        xp_bonus = min(self._xp.unique_spell_count(player_id) * bonuses.xp_per_unique_spell, bonuses.xp_max)
        cadence_bonus = self._cadence_bonus(stroke) * bonuses.cadence_max
        tempo_bonus = self._tempo_bonus(stroke.duration_s)

        subtotal = base + xp_bonus + cadence_bonus + tempo_bonus
        natural_quality = self._resolve_quality(subtotal)

        # Pity bonus only when the cast (gate-passing) fell short of the lowest tier.
        streak_bonus = 0.0
        pity_pass = False
        total = subtotal
        quality = natural_quality

        if natural_quality is None:
            streak_bonus = self._streak.failed_streak(player_id) * bonuses.streak_per_fail
            total = subtotal + streak_bonus
            if total >= self._lowest_threshold:
                quality = self._lowest_tier  # clamp: pity never awards above the lowest tier
                pity_pass = True

        return CastScore(
            label=label,
            match_accuracy=match_accuracy,
            base=base,
            xp_bonus=xp_bonus,
            cadence_bonus=cadence_bonus,
            tempo_bonus=tempo_bonus,
            streak_bonus=streak_bonus,
            difficulty_weight=difficulty,
            total=total,
            quality=quality,
            passed_gates=True,
            pity_pass=pity_pass,
        )

    def apply_outcome(self, player_id: str, cast: CastScore) -> None:
        """Update per-player state from a scored cast: reset streak + accrue XP on success,
        else extend the failure streak."""
        if cast.recognized:
            self._streak.reset(player_id)
            self._xp.record_cast(player_id, cast.label)
        else:
            self._streak.record_fail(player_id)

    def _cadence_bonus(self, stroke: Stroke) -> float:
        """0..1 smoothness: low coefficient of variation of per-sample speed = even draw."""
        points = stroke.points
        times = stroke.times_ms
        if len(points) < 3:
            return 0.0

        speeds: list[float] = []
        for i in range(1, len(points)):
            dt = (times[i] - times[i - 1]) / 1000.0
            if dt <= 0:
                continue
            speeds.append(math.dist(points[i - 1], points[i]) / dt)

        if len(speeds) < 2:
            return 0.0

        mean = sum(speeds) / len(speeds)
        if mean <= 0:
            return 0.0
        variance = sum((s - mean) ** 2 for s in speeds) / len(speeds)
        cv = math.sqrt(variance) / mean  # coefficient of variation
        return max(0.0, 1.0 - cv)

    def _tempo_bonus(self, duration_s: float) -> float:
        b = self._settings.bonuses
        if b.tempo_ideal_min_s <= duration_s <= b.tempo_ideal_max_s:
            return b.tempo_max
        if duration_s < b.tempo_ideal_min_s:
            gap = b.tempo_ideal_min_s - duration_s
        else:
            gap = duration_s - b.tempo_ideal_max_s
        decay = max(0.0, 1.0 - gap / b.tempo_decay_s) if b.tempo_decay_s > 0 else 0.0
        return b.tempo_max * decay

    def _resolve_quality(self, total: float) -> SpellCastQuality | None:
        best: SpellCastQuality | None = None
        best_threshold = float("-inf")
        for quality, threshold in self._settings.quality_thresholds.items():
            if total >= threshold and threshold > best_threshold:
                best = quality
                best_threshold = threshold
        return best
