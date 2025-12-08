import random
from dataclasses import dataclass

from spells.accuracy.configuration.accuracy_scorer_settings import SpellAccuracyScorerSettings
from spells.accuracy.spell_accuracy_weights_settings import SpellAccuracyWeightsSettings
from spells.matching.spell_match_metrics import SpellMatchMetrics
from spells.spell_definition import SpellDefinition


@dataclass
class SpellAccuracyBreakdown:
    score: float
    count_score: float
    distance_score: float
    duration_score: float


class SpellAccuracyScorer:
    def __init__(self, settings: SpellAccuracyScorerSettings) -> None:
        self._settings = settings

    def calculate(self, spell: SpellDefinition, metrics: SpellMatchMetrics) -> SpellAccuracyBreakdown:
        """
        Compute an overall accuracy score in [0,1] plus its component scores.

        - count_score    → based on required/optional coverage
        - distance_score → how well distance ratios match relative_distance
        - duration_score → how well duration ratios match relative_duration
        """

        weights = self._settings.weights

        count_s = _count_score(spell, metrics, weights)
        dist_s = _distance_score(spell, metrics)
        dur_s = _duration_score(spell, metrics)

        total_w = weights.step_count_weight + weights.relative_group_distance_weight + weights.relative_group_duration_weight
        if total_w <= 0:
            overall = 0.0
        else:
            overall = (
                weights.step_count_weight * count_s
                + weights.relative_group_distance_weight * dist_s
                + weights.relative_group_duration_weight * dur_s
            ) / total_w

        d = random.randrange(0, 10) / 1000
        f = random.randrange(0, self._settings.fudge) / 100
        sign = random.choice((-1, 1))

        overall = overall + (sign * (d + f))

        if overall <= 0:
            overall = f + d

        if overall >= 100:
            overall = 100 - (f + d)

        return SpellAccuracyBreakdown(
            score=overall,
            count_score=count_s,
            distance_score=dist_s,
            duration_score=dur_s,
        )


def _safe_div(num: float, den: float, default: float = 1.0) -> float:
    return num / den if den > 0 else default


def _count_score(spell: SpellDefinition, metrics: SpellMatchMetrics, weights: SpellAccuracyWeightsSettings) -> float:
    # Required coverage: 1.0 only if all required matched
    req_frac = _safe_div(metrics.required_matched, metrics.required_total, default=1.0)

    # Optional coverage: if there are no optionals, treat as "full" (1.0)
    opt_frac = _safe_div(metrics.optional_matched, metrics.optional_total, default=1.0)

    # Weighted blend: bias towards required coverage
    rb = weights.required_step_bias
    return rb * req_frac + (1.0 - rb) * opt_frac


def _ratio_score_per_group(
    targets: dict[int, float],
    actuals: dict[int, float],
    tol: float,
) -> float:
    """
    Compute a [0,1] score from target vs actual ratios on a per-group basis.

    For each group i:

        err_i   = |actual_i - target_i|
        norm_i  = min(err_i / tol, 1.0)
        score_i = 1.0 - norm_i

    Then return the mean score_i over all groups that have a target.
    """
    if not targets:
        return 1.0  # nothing to compare → neutral

    if tol <= 0:
        # Degenerate case: treat exact match as 1.0, anything else as 0.0
        scores = []
        for gi, target in targets.items():
            actual = actuals.get(gi, 0.0)
            scores.append(1.0 if abs(actual - target) < 1e-6 else 0.0)
        return sum(scores) / len(scores) if scores else 1.0

    scores = []
    for gi, target in targets.items():
        actual = actuals.get(gi, 0.0)
        err = abs(actual - target)
        norm = min(err / tol, 1.0)
        scores.append(1.0 - norm)

    return sum(scores) / len(scores) if scores else 1.0


def _distance_score(spell: SpellDefinition, metrics: SpellMatchMetrics) -> float:
    # Build target & actual ratios per group, based on distance
    total = max(metrics.total_distance, spell.group_distance_min_total)

    targets: dict[int, float] = {}
    actuals: dict[int, float] = {}

    for gi, group in enumerate(spell.step_groups):
        target = getattr(group, "relative_distance", None)
        if target is None:
            continue
        targets[gi] = target
        actuals[gi] = metrics.group_distance[gi] / total

    tol = spell.group_distance_rel_tol
    return _ratio_score_per_group(targets, actuals, tol)


def _duration_score(spell: SpellDefinition, metrics: SpellMatchMetrics) -> float:
    # Build target & actual ratios per group, based on duration
    total = max(metrics.total_duration_s, spell.group_duration_min_total_s)

    targets: dict[int, float] = {}
    actuals: dict[int, float] = {}

    for gi, group in enumerate(spell.step_groups):
        target = getattr(group, "relative_duration", None)
        if target is None:
            continue
        targets[gi] = target
        actuals[gi] = metrics.group_duration_s[gi] / total

    tol = spell.group_duration_rel_tol
    return _ratio_score_per_group(targets, actuals, tol)
