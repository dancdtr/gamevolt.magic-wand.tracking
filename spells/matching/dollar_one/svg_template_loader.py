"""Load a layered spell SVG as an ordered point list for use as a $1 template.

Expected layer convention (Illustrator: Object IDs = Layer Names):
  - `gesture`  : the template <path>. Its `d` defines the geometry.
  - `origin`   : a marker (circle) at the canonical gesture START. Optional.
  - `arrows`   : UI-only direction art. Ignored here.

The path's `d` order *would* define cast direction (M = start), but Illustrator
exports paths in either direction. When an `origin` marker is present we orient
the sampled points so they START at the endpoint nearest the marker — so a
reversed export self-corrects and no per-file fixing is needed.

SVG y grows downward; wand forward-vector y grows upward, so we flip y on import
(both the path samples and the origin marker, keeping them in one space).
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

from svgpathtools import parse_path

Point = tuple[float, float]

# Layer-id keywords (substring, case-insensitive). `gesture` also matches `gestures`.
_GESTURE_KEY = "gesture"
_ORIGIN_KEY = "origin"


def load_svg_points(svg_path: Path, samples: int = 256) -> list[Point]:
    """Sample the gesture path evenly by arc length, oriented by the origin marker."""
    root = ET.parse(str(svg_path)).getroot()

    d = _gesture_d(root)
    if d is None:
        raise ValueError(f"no gesture <path> found in {svg_path}")

    points = _sample(parse_path(d), samples)

    origin = _origin_point(root)
    if origin is not None and len(points) >= 2:
        if math.dist(points[-1], origin) < math.dist(points[0], origin):
            points.reverse()

    return points


def _sample(path, samples: int) -> list[Point]:
    """Sample `samples` points evenly by arc length, y-flipped to wand space."""
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


def _local(tag: str) -> str:
    """Strip XML namespace: '{http://...}path' -> 'path'."""
    return tag.rsplit("}", 1)[-1]


def _groups(root: ET.Element):
    for el in root.iter():
        if _local(el.tag) == "g":
            yield el


def _element_d(el: ET.Element) -> str | None:
    """A parse_path-able `d` for a geometry element (path/polyline/polygon/line)."""
    tag = _local(el.tag)
    if tag == "path":
        return el.get("d")
    if tag in ("polyline", "polygon"):
        nums = (el.get("points") or "").replace(",", " ").split()
        coords = list(zip(nums[0::2], nums[1::2]))
        if not coords:
            return None
        d = "M " + " L ".join(f"{x},{y}" for x, y in coords)
        return d + " Z" if tag == "polygon" else d
    if tag == "line":
        return f"M {el.get('x1', 0)},{el.get('y1', 0)} L {el.get('x2', 0)},{el.get('y2', 0)}"
    return None


def _first_geometry_d(el: ET.Element) -> str | None:
    for child in el.iter():
        d = _element_d(child)
        if d:
            return d
    return None


def _gesture_d(root: ET.Element) -> str | None:
    """`d` of the gesture-layer geometry; fall back to the first geometry anywhere."""
    for g in _groups(root):
        if _GESTURE_KEY in (g.get("id") or "").lower():
            d = _first_geometry_d(g)
            if d:
                return d
    return _first_geometry_d(root)  # back-compat: un-layered single-shape templates


def _origin_point(root: ET.Element) -> Point | None:
    """Origin marker as a y-flipped point, or None if no origin layer/marker."""
    for g in _groups(root):
        if _ORIGIN_KEY not in (g.get("id") or "").lower():
            continue
        for el in g.iter():
            tag = _local(el.tag)
            if tag in ("circle", "ellipse"):
                return (float(el.get("cx", 0.0)), -float(el.get("cy", 0.0)))
            if tag == "path":
                z = parse_path(el.get("d", "")).point(0.0)
                return (z.real, -z.imag)
    return None
