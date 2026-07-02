"""Load a layered spell SVG as an ordered point list for use as a $1 template.

Required layer convention (Illustrator: Object IDs = Layer Names):
  - `gesture_path`   : the true centreline geometry. MUST be a single open shape
                       (<path>, or a straight-segment <polyline>/<line> as Illustrator
                       exports one); its geometry defines the sampled curve fed to $1.
                       This is what the recognizer matches against — never the visual
                       stroke.
  - `gesture_visual` : the prettied stroke shown to the user (may use a width
                       profile / be a filled outline). UX-only, ignored here.
  - `origin`         : marker at the canonical gesture START. Required.
  - `end_arrow`      : marker at the canonical gesture END. Required. Also drawn in
                       the spell result visualiser.
  - `mid_arrows`     : decorative direction hints. UX-only, ignored here.
  - `bg`             : editor-only backdrop. Ignored here.

A width-profiled or filled `gesture_visual` exports as an *outline* (down one edge,
back the other) — a there-and-back that $1 cannot match. `gesture_path` exists to
carry the clean centreline instead; keep it an open, unstroked-outline path.

A layered SVG that is missing `origin`, missing `end_arrow`, or whose `gesture_path`
is not exactly one shape is *invalid* and raises `ValueError` — a broken
template silently degrades the cast experience, so we fail loud and force the
author to fix it (or exclude the spell knowingly upstream).

Illustrator exports paths in either direction, so `d` order is not trustworthy.
We orient the sampled points using both markers: points START nearest `origin`
and END nearest `end_arrow`. Marker/geometry disagreements are warned, not fatal.

SVG y grows downward; wand forward-vector y grows upward, so we flip y on import
(path samples and both markers, keeping them in one space).
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from svgpathtools import parse_path

from gamevolt.logging import Logger

Point = tuple[float, float]

# Layer-id keywords (substring, case-insensitive). `gesture_path` deliberately does
# not match the UI-only `gesture_visual`; `mid_arrows` does not match `end_arrow`.
_GESTURE_KEY = "gesture_path"
_ORIGIN_KEY = "origin"
_END_KEY = "end_arrow"

# Moveto commands split a `d` into subpaths; $1 expects one continuous stroke.
_MOVETO = re.compile(r"[Mm]")


def load_svg_points(svg_path: Path, samples: int = 256, logger: Logger | None = None) -> list[Point]:
    """Sample the gesture path evenly by arc length, oriented by origin + end_arrow.

    Raises `ValueError` if the template is invalid (no origin, no end_arrow, or a
    gesture that is not a single <path>). Malformed-but-usable geometry is warned.
    """
    root = ET.parse(str(svg_path)).getroot()

    d = _gesture_d(root)  # raises if gesture layer is missing or not a single path
    origin = _marker_point(root, _ORIGIN_KEY)
    if origin is None:
        raise ValueError("missing required `origin` marker")
    end = _marker_point(root, _END_KEY)
    if end is None:
        raise ValueError("missing required `end_arrow` marker")

    path = parse_path(d)
    _warn_if_malformed(path, d, logger)

    points = _sample(path, samples)
    _orient(points, origin, end, logger)
    return points


def _sample(path, samples: int) -> list[Point]:
    """Sample `samples` points evenly by arc length, y-flipped to wand space.

    Builds an arc-length table from dense uniform-`t` subsamples and interpolates,
    instead of calling svgpathtools' `ilength` per point. `ilength` inverts arc
    length with Newton iteration and raises on some valid curves — endpoint
    overshoot ("s is not in interval [0, curve.length()]") or non-convergence on
    tight/near-degenerate segments ("Maximum iterations reached"). The table is
    numerically robust and covers any template geometry.
    """
    if path.length() <= 0:
        z = path.point(0.0)
        return [(z.real, -z.imag)] * samples

    # Dense subsamples in parameter t, with cumulative chord length as arc length.
    sub = max(samples * 8, 2048)
    ts = [i / sub for i in range(sub + 1)]
    pts = [path.point(t) for t in ts]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + abs(b - a))
    total = cum[-1]

    points: list[Point] = []
    j = 0
    for i in range(samples):
        target = total * i / (samples - 1)
        while j < sub - 1 and cum[j + 1] < target:
            j += 1
        seg = cum[j + 1] - cum[j]
        frac = 0.0 if seg <= 0 else (target - cum[j]) / seg
        z = pts[j] + (pts[j + 1] - pts[j]) * frac  # linear interp between dense samples
        points.append((z.real, -z.imag))  # y-flip: SVG y-down -> wand y-up
    return points


def _orient(points: list[Point], origin: Point, end: Point, logger: Logger | None) -> None:
    """Reverse `points` in place so they start nearest `origin`, end nearest `end_arrow`."""
    if len(points) < 2:
        return

    start_pt, end_pt = points[0], points[-1]
    forward = math.dist(start_pt, origin) + math.dist(end_pt, end)
    reverse = math.dist(end_pt, origin) + math.dist(start_pt, end)
    if reverse < forward:
        points.reverse()

    # After best-fit orientation the origin should still sit nearer the start and
    # end_arrow nearer the finish; if not, the markers likely disagree with the path.
    s, e = points[0], points[-1]
    if math.dist(s, origin) > math.dist(e, origin) or math.dist(e, end) > math.dist(s, end):
        if logger is not None:
            logger.warning("$1: origin/end_arrow markers are inconsistent with the gesture endpoints")


def _warn_if_malformed(path, d: str, logger: Logger | None) -> None:
    """Warn about geometry that $1 may mismatch on, without failing the load."""
    if logger is None:
        return
    if path.length() <= 0:
        logger.warning("$1: gesture path has zero length")
    if len(_MOVETO.findall(d)) > 1:
        logger.warning("$1: gesture has multiple subpaths; $1 expects a single continuous stroke")


def _local(tag: str) -> str:
    """Strip XML namespace: '{http://...}path' -> 'path'."""
    return tag.rsplit("}", 1)[-1]


def _groups(root: ET.Element):
    for el in root.iter():
        if _local(el.tag) == "g":
            yield el


def _layer(root: ET.Element, key: str) -> ET.Element | None:
    """First <g> whose id contains `key` (case-insensitive)."""
    for g in _groups(root):
        if key in (g.get("id") or "").lower():
            return g
    return None


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


_GESTURE_SHAPES = ("path", "polyline", "polygon", "line")


def _gesture_d(root: ET.Element) -> str:
    """`d` of the `gesture_path` layer's single geometry element.

    Accepts a lone <path>/<polyline>/<polygon>/<line> — Illustrator exports a
    straight-segment centreline as <polyline>, which is a valid single stroke.
    Raises if the layer is absent or holds anything other than exactly one shape.
    """
    layer = _layer(root, _GESTURE_KEY)
    if layer is None:
        raise ValueError("missing required `gesture_path` layer")

    shapes = [el for el in layer.iter() if _local(el.tag) in _GESTURE_SHAPES]
    if len(shapes) != 1:
        raise ValueError(f"`gesture_path` must be a single shape (found {len(shapes)})")

    d = _element_d(shapes[0])
    if not d:
        raise ValueError(f"`gesture_path` <{_local(shapes[0].tag)}> has no usable geometry")
    return d


def _marker_point(root: ET.Element, key: str) -> Point | None:
    """Representative y-flipped point for a marker layer, or None if the layer is absent.

    Circle/ellipse -> centre; any other geometry -> bounding-box centre (stable for
    an arbitrary arrow glyph, unlike a single path vertex).
    """
    layer = _layer(root, key)
    if layer is None:
        return None

    for el in layer.iter():
        tag = _local(el.tag)
        if tag in ("circle", "ellipse"):
            return (float(el.get("cx", 0.0)), -float(el.get("cy", 0.0)))

    d = _first_geometry_d(layer)
    if d:
        xmin, xmax, ymin, ymax = parse_path(d).bbox()
        return ((xmin + xmax) / 2.0, -(ymin + ymax) / 2.0)
    return None
