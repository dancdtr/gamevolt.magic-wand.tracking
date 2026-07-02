"""Generated gesture-difficulty rating (1–10) per spell.

Distinct from the lore `SpellInfo.difficulty` string (the Primer's "Beginner /
Intermediate / Advanced" flavour text). This is a *computed* score: how hard the
spell is to actually cast, from two inputs the player feels —

  1. **shape** of the gesture centreline (`gesture_path`): how much it turns, how
     folded it is, how many sharp corners. Pure geometry, from arc-length samples.
  2. **pass thresholds** from scoring settings: `min_match_accuracy` (how tight the
     $1 match must be to even register) and the `MASTERED` quality threshold (how
     high you must score to top-tier). A spell tuned lenient (e.g. Alohomora,
     Reparo) reads easier even if its shape is busy.

Normalisation is **absolute** (fixed bounds calibrated from the catalogue in
`_ShapeBounds` / `_ThresholdBounds`), not percentile — a spell's rating must not
drift because a *different* template was edited. Bounds assume ~128 arc-length
samples (`_SAMPLES`).

Product-only, like lore/selection: the rating is UX/curation and never gates a
cast. An unloadable template (e.g. a `gesture_path` still authored as a polyline)
degrades to threshold-only rather than raising — see `difficulty_for_template`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from gamevolt.logging import Logger
from spells.matching.dollar_one.svg_template_loader import Point, load_svg_points

_SAMPLES = 128
_CUSP_ANGLE = math.radians(50)  # per-step turn above this counts as a sharp corner


def _norm(value: float, lo: float, hi: float) -> float:
    """Clamp `value` into [lo, hi], returned as a 0..1 fraction."""
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


@dataclass(frozen=True)
class _ShapeBounds:
    """Absolute lo/hi per shape metric — calibrated from the template catalogue
    (≈p5..p95 so typical spells spread across the range, extremes clamp)."""

    turning_lo: float = 0.5   # total turning / pi  (straight ≈ 0, one loop = 2)
    turning_hi: float = 6.0
    density_lo: float = 1.0   # path length / bbox diagonal (straight = 1)
    density_hi: float = 4.0
    cusps_lo: float = 0.0     # count of sharp corners
    cusps_hi: float = 5.0


@dataclass(frozen=True)
class _ThresholdBounds:
    accuracy_lo: float = 0.30   # min_match_accuracy: lenient .3 -> strict .7
    accuracy_hi: float = 0.70
    mastered_lo: float = 60.0   # MASTERED quality threshold
    mastered_hi: float = 120.0


@dataclass(frozen=True)
class DifficultyWeights:
    """Blend weights. `shape` vs `threshold` split the final rating; the sub-weights
    within each component sum to 1 (renormalised if not)."""

    shape: float = 0.65
    threshold: float = 0.35
    # shape sub-weights
    turning: float = 0.5
    density: float = 0.3
    cusps: float = 0.2
    # threshold sub-weights
    accuracy: float = 0.5
    mastered: float = 0.5

    shape_bounds: _ShapeBounds = _ShapeBounds()
    threshold_bounds: _ThresholdBounds = _ThresholdBounds()


DEFAULT_WEIGHTS = DifficultyWeights()


def _shape_metrics(points: list[Point]) -> tuple[float, float, int]:
    """(total_turning/pi, length/bbox_diagonal, cusp_count) for a sampled stroke."""
    n = len(points)
    if n < 3:
        return 0.0, 1.0, 0

    turning = 0.0
    cusps = 0
    length = 0.0
    for i in range(1, n):
        length += math.dist(points[i], points[i - 1])
    for i in range(1, n - 1):
        ax, ay = points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]
        bx, by = points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1]
        step = abs((math.atan2(by, bx) - math.atan2(ay, ax) + math.pi) % (2 * math.pi) - math.pi)
        turning += step
        if step > _CUSP_ANGLE:
            cusps += 1

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    return turning / math.pi, length / diag, cusps


def shape_complexity(points: list[Point], weights: DifficultyWeights = DEFAULT_WEIGHTS) -> float:
    """0..1 complexity of a gesture centreline from its arc-length samples."""
    turning, density, cusps = _shape_metrics(points)
    b = weights.shape_bounds
    parts = (
        (weights.turning, _norm(turning, b.turning_lo, b.turning_hi)),
        (weights.density, _norm(density, b.density_lo, b.density_hi)),
        (weights.cusps, _norm(cusps, b.cusps_lo, b.cusps_hi)),
    )
    return _blend(parts)


def threshold_difficulty(
    min_match_accuracy: float,
    mastered_threshold: float,
    weights: DifficultyWeights = DEFAULT_WEIGHTS,
) -> float:
    """0..1 difficulty from the spell's scoring gates/tiers."""
    b = weights.threshold_bounds
    parts = (
        (weights.accuracy, _norm(min_match_accuracy, b.accuracy_lo, b.accuracy_hi)),
        (weights.mastered, _norm(mastered_threshold, b.mastered_lo, b.mastered_hi)),
    )
    return _blend(parts)


def _blend(parts: tuple[tuple[float, float], ...]) -> float:
    """Weighted mean of (weight, value) pairs; renormalises the weights."""
    total_w = sum(w for w, _ in parts)
    if total_w <= 0:
        return 0.0
    return sum(w * v for w, v in parts) / total_w


def _to_rating(combined: float) -> float:
    """Map a 0..1 blend onto the 1–10 scale (nothing is 0-difficulty), 1 d.p."""
    return round(1.0 + 9.0 * max(0.0, min(1.0, combined)), 1)


def gesture_difficulty(
    points: list[Point],
    *,
    min_match_accuracy: float,
    mastered_threshold: float,
    weights: DifficultyWeights = DEFAULT_WEIGHTS,
) -> float:
    """Full 1–10 rating: blend shape complexity with pass-threshold difficulty."""
    shape = shape_complexity(points, weights)
    thresh = threshold_difficulty(min_match_accuracy, mastered_threshold, weights)
    combined = _blend(((weights.shape, shape), (weights.threshold, thresh)))
    return _to_rating(combined)


def difficulty_for_template(
    svg_path: Path,
    *,
    min_match_accuracy: float,
    mastered_threshold: float,
    weights: DifficultyWeights = DEFAULT_WEIGHTS,
    logger: Logger | None = None,
) -> float:
    """1–10 rating for a template file. Fail-soft: if the SVG can't be sampled (bad
    `gesture_path`), fall back to a threshold-only rating so callers still get a
    number — difficulty is product-only and must never break on a template."""
    try:
        points = load_svg_points(svg_path, _SAMPLES, logger)
    except Exception as exc:  # noqa: BLE001 — product-only rating must never break on a template
        # ValueError (bad gesture_path), OSError (missing file), or svgpathtools
        # arc-length blowups all fall back to a threshold-only number.
        if logger is not None:
            logger.debug(f"difficulty: {svg_path.name} not sampleable ({exc}); threshold-only rating")
        thresh = threshold_difficulty(min_match_accuracy, mastered_threshold, weights)
        return _to_rating(thresh)
    return gesture_difficulty(
        points,
        min_match_accuracy=min_match_accuracy,
        mastered_threshold=mastered_threshold,
        weights=weights,
    )
