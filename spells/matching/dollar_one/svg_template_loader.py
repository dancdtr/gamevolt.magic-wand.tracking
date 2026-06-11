"""Load an SVG `<path>` as an ordered point list for use as a $1 template.

The path's `d` order defines the cast direction (M = gesture start). SVG y grows
downward; wand forward-vector y grows upward, so we flip y on import.
"""

from __future__ import annotations

from pathlib import Path

from svgpathtools import svg2paths

Point = tuple[float, float]


def load_svg_points(svg_path: Path, samples: int = 256) -> list[Point]:
    """Sample the first path in an SVG file evenly by arc length."""
    paths, _ = svg2paths(str(svg_path))
    if not paths:
        raise ValueError(f"no <path> found in {svg_path}")

    path = paths[0]
    total_length = path.length()

    points: list[Point] = []
    for i in range(samples):
        if total_length > 0:
            distance = total_length * i / (samples - 1)
            z = path.point(path.ilength(distance))
        else:
            z = path.point(0.0)
        points.append((z.real, -z.imag))  # y-flip: SVG y-down -> wand y-up
    return points
