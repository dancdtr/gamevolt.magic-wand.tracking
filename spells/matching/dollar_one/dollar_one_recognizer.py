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


def match_score(candidate_prepared: list[Point], template_prepared: list[Point]) -> float:
    """0..1 similarity. Both inputs must already be `prepare`d to the same point count."""
    return max(0.0, 1.0 - _path_distance(candidate_prepared, template_prepared) / _HALF_DIAGONAL)


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
