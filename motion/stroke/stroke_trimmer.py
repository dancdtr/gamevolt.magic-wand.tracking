"""Detects and trims the straight run at either end of a stroke.

People hold the wand out (that orientation becomes the path origin) then move in a
straight line to where the glyph actually starts before drawing it — the lead-in
(approach). They often also run straight back toward rest/centre afterwards before
pausing — the tail (reset). Both pollute $1 matching and the template overlay.

Such a run is a *straight* segment ending in a *sharp corner* (the glyph edge). We find
the first corner — a local spike in per-step turning angle — and cut there. A smoothly
curving glyph (e.g. a circle) has only gentle, continuous turning and no sharp corner, so
nothing is trimmed. The `min_trim_fraction` guard also ignores corners that sit right at
the edge (a glyph that simply begins or ends with a corner, no approach/reset).

`lead_in_cut_index` works from the start; `tail_cut_index` is its mirror, finding the
reset run from the end by running the same detector over the reversed path.
"""

from __future__ import annotations

import math

from motion.stroke.configuration.stroke_trim_settings import StrokeTrimSettings

Point = tuple[float, float]


def lead_in_cut_index(points: list[Point], settings: StrokeTrimSettings) -> int:
    """Index into `points` where the glyph begins; 0 means trim nothing."""
    n = len(points)
    if not settings.enabled or n < 12:
        return 0

    res = _resample(points, settings.resample_count)
    m = len(res)
    step = max(1, m // 24)
    if m <= 2 * step + 1:
        return 0

    threshold = math.radians(settings.angle_deg)

    corner: int | None = None
    for i in range(step, m - step):
        turning = _angle_diff(_heading(res[i - step], res[i]), _heading(res[i], res[i + step]))
        if turning > threshold:
            corner = i
            break
    if corner is None:
        return 0

    frac = corner / (m - 1)
    if frac < settings.min_trim_fraction:
        return 0
    frac = min(frac, settings.max_trim_fraction)

    return _index_at_arc_fraction(points, frac)


def tail_cut_index(points: list[Point], settings: StrokeTrimSettings) -> int:
    """Index into `points` (exclusive end) where the glyph ends; len(points) trims nothing.

    Mirror of `lead_in_cut_index`. After drawing, people often run the wand back toward
    their rest/centre orientation before pausing — a straight 'reset' tail that pollutes
    matching exactly like an approach lead-in, only at the other end. It has the same
    shape reversed (straight run ending in a sharp corner = the glyph's last point), so we
    detect it by running the lead-in finder over the reversed path and mapping the cut back.
    """
    n = len(points)
    cut = lead_in_cut_index(list(reversed(points)), settings)
    if cut <= 0:
        return n
    return n - cut


def _resample(points: list[Point], n: int) -> list[Point]:
    if len(points) < 2 or n < 2:
        return list(points)
    total = _path_length(points)
    if total <= 0:
        return list(points)

    interval = total / (n - 1)
    out: list[Point] = [points[0]]
    acc = 0.0
    i = 1
    prev = points[0]
    while i < len(points) and len(out) < n:
        d = math.dist(prev, points[i])
        if acc + d >= interval and d > 0:
            t = (interval - acc) / d
            nx = prev[0] + t * (points[i][0] - prev[0])
            ny = prev[1] + t * (points[i][1] - prev[1])
            out.append((nx, ny))
            prev = (nx, ny)
            acc = 0.0
        else:
            acc += d
            prev = points[i]
            i += 1
    while len(out) < n:
        out.append(points[-1])
    return out


def _index_at_arc_fraction(points: list[Point], frac: float) -> int:
    total = _path_length(points)
    if total <= 0:
        return 0
    target = frac * total
    acc = 0.0
    for i in range(1, len(points)):
        acc += math.dist(points[i - 1], points[i])
        if acc >= target:
            return i
    return 0


def _path_length(points: list[Point]) -> float:
    return sum(math.dist(points[i - 1], points[i]) for i in range(1, len(points)))


def _heading(a: Point, b: Point) -> float:
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _angle_diff(h: float, ref: float) -> float:
    d = abs(h - ref) % (2 * math.pi)
    return min(d, 2 * math.pi - d)
