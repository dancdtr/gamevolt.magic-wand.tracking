"""$1 unistroke recognizer (Wobbrock et al.), tuned for wand gestures.

Two deliberate departures from textbook $1:
  - NO rotation step. Wand gestures are orientation-meaningful (up-flick != down-flick),
    so we skip the indicative-angle / golden-section rotation that makes $1 rotation-invariant.
  - Uniform scale (not non-uniform unit-box). Avoids the classic $1 blow-up on near-1D
    line gestures whose bounding box has ~zero area in one dimension.

Stroke direction (point order) IS preserved, so $1 (not $P/$Q) is the right family.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Point = tuple[float, float]

# Half-diagonal of a unit bounding box; the scale we normalise the longest axis to.
_HALF_DIAGONAL = 0.5 * math.sqrt(2.0)


def _path_length(points: list[Point]) -> float:
    return sum(math.dist(points[i - 1], points[i]) for i in range(1, len(points)))


def resample(points: list[Point], n: int) -> list[Point]:
    """Resample a path to exactly `n` points evenly spaced by arc length."""
    if len(points) < 2:
        return [points[0]] * n if points else []

    interval = _path_length(points) / (n - 1)
    if interval <= 0:
        return [points[0]] * n

    out: list[Point] = [points[0]]
    pts = list(points)
    accumulated = 0.0
    i = 1
    while i < len(pts):
        p0, p1 = pts[i - 1], pts[i]
        d = math.dist(p0, p1)
        if accumulated + d >= interval:
            t = (interval - accumulated) / d if d > 0 else 0.0
            q = (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1]))
            out.append(q)
            pts.insert(i, q)  # continue measuring from the inserted point
            accumulated = 0.0
        else:
            accumulated += d
        i += 1

    # Floating-point drift can leave us one short.
    while len(out) < n:
        out.append(points[-1])
    return out[:n]


def _centroid(points: list[Point]) -> Point:
    n = len(points)
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)


def normalize(points: list[Point]) -> list[Point]:
    """Translate centroid to origin, then uniform-scale longest axis to 1."""
    cx, cy = _centroid(points)
    centred = [(p[0] - cx, p[1] - cy) for p in points]

    xs = [p[0] for p in centred]
    ys = [p[1] for p in centred]
    scale = max(max(xs) - min(xs), max(ys) - min(ys))
    if scale < 1e-9:
        return centred
    return [(p[0] / scale, p[1] / scale) for p in centred]


def prepare(points: list[Point], n: int = 64) -> list[Point]:
    return normalize(resample(points, n))


def _path_distance(a: list[Point], b: list[Point]) -> float:
    return sum(math.dist(a[i], b[i]) for i in range(len(a))) / len(a)


# Direction is sampled over an n/8 spacing (not adjacent points): wide enough to
# suppress per-sample jitter, short enough to keep local shape (loop vs line).
_DIRECTION_STRIDE_FRAC = 8


def _direction_angles(points: list[Point], stride: int) -> list[float]:
    return [
        math.atan2(points[i + stride][1] - points[i][1], points[i + stride][0] - points[i][0])
        for i in range(len(points) - stride)
    ]


def _angular_distance(a: float, b: float) -> float:
    """Smallest absolute angle between two headings, handling wraparound. 0..pi."""
    return abs((a - b + math.pi) % (2.0 * math.pi) - math.pi)


def _direction_score(a: list[Point], b: list[Point]) -> float:
    """0..1 heading similarity. Separates loop-vs-line that positional distance misses."""
    stride = max(1, len(a) // _DIRECTION_STRIDE_FRAC)
    da = _direction_angles(a, stride)
    db = _direction_angles(b, stride)
    if not da:
        return 1.0
    mean = sum(_angular_distance(x, y) for x, y in zip(da, db)) / len(da)
    return max(0.0, 1.0 - mean / math.pi)


def _position_score(a: list[Point], b: list[Point]) -> float:
    return max(0.0, 1.0 - _path_distance(a, b) / _HALF_DIAGONAL)


def _coverage_score(candidate: list[Point], template: list[Point]) -> float:
    """0..1: how much of the template the candidate actually visits.

    Mean nearest-candidate distance per template point. One-directional on purpose:
    template regions the trace never goes near drag this down, while honest wobble
    around the glyph barely moves it. Punishes drawing only one leg of a multi-leg
    glyph (e.g. just the diagonal of a Z), which index-wise distance underweights.
    """
    mean = sum(min(math.dist(t, c) for c in candidate) for t in template) / len(template)
    return max(0.0, 1.0 - mean / _HALF_DIAGONAL)


def _shortfall_score(candidate: list[Point], template: list[Point]) -> float:
    """0..1: normalised arc-length of the candidate relative to the template, capped at 1.

    Both inputs are unit-box normalised, so this compares shape complexity, not size.
    A single leg of a multi-leg glyph is far shorter than the whole glyph and scores
    low; only under-drawing is punished — jitter-inflated overshoot stays at 1 so a
    wobbly-but-complete trace is not penalised.
    """
    lt = _path_length(template)
    if lt <= 0:
        return 1.0
    return min(1.0, _path_length(candidate) / lt)


def match_score(candidate_prepared: list[Point], template_prepared: list[Point]) -> float:
    """0..1 similarity. Both inputs must already be `prepare`d to the same point count.

    Product of four terms:
      - position: point-by-point distance. Alone it is too forgiving — a straight
        swipe scores ~0.6 against a looped glyph.
      - direction: heading agreement. Collapses loop-vs-line mismatches.
      - coverage: template points must be near *some* candidate point, so skipping
        whole legs of a glyph costs heavily.
      - shortfall: candidate normalised arc-length must reach the template's, so a
        single stroke of a multi-stroke glyph (the Z-diagonal cheat) cannot pass.

    Accurate-but-wobbly full traces stay high (all four terms are jitter-tolerant);
    partial traces collapse via coverage x shortfall.
    """
    return (
        _position_score(candidate_prepared, template_prepared)
        * _direction_score(candidate_prepared, template_prepared)
        * _coverage_score(candidate_prepared, template_prepared)
        * _shortfall_score(candidate_prepared, template_prepared)
    )


@dataclass(frozen=True)
class PathTemplate:
    label: str
    points: list[Point]  # already prepared (resampled + normalized)


@dataclass(frozen=True)
class Recognition:
    label: str
    score: float


class DollarOneRecognizer:
    def __init__(self, templates: list[PathTemplate], n: int = 64) -> None:
        self._templates = templates
        self._n = n

    @property
    def template_count(self) -> int:
        return len(self._templates)

    def template_points(self, label: str) -> list[Point]:
        """Prepared (resampled + normalised) points for a template label; [] if unknown."""
        for t in self._templates:
            if t.label == label:
                return list(t.points)
        return []

    def prepare_points(self, points: list[Point]) -> list[Point]:
        """Prepare raw candidate points the same way `recognize` does (resample + normalise)."""
        if len(points) < 2:
            return []
        return prepare(points, self._n)

    def recognize(self, points: list[Point], allowed: set[str] | None = None) -> list[Recognition]:
        """Score raw candidate points against templates, best first.

        `allowed` restricts scoring to those template labels (the zone-active spell set).
        None = score every template (dev/diagnostic use). An empty set = no candidates.
        """
        if len(points) < 2:
            return []

        templates = self._templates if allowed is None else [t for t in self._templates if t.label in allowed]
        if not templates:
            return []

        candidate = prepare(points, self._n)
        results = [Recognition(t.label, match_score(candidate, t.points)) for t in templates]
        results.sort(key=lambda r: r.score, reverse=True)
        return results
