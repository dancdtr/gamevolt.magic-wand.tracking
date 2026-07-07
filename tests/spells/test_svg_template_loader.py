"""Closed-gesture rejection: a `z`-closed `gesture_path` is the signature of a
filled/outlined stroke export (a there-and-back $1 cannot match), so the loader
must fail loud instead of building an unmatchable template."""

from pathlib import Path

import pytest

from spells.matching.dollar_one.svg_template_loader import load_svg_points


def _svg(gesture: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <g id="gesture_path">{gesture}</g>
  <g id="origin"><circle cx="10" cy="10" r="2"/></g>
  <g id="end_arrow"><circle cx="90" cy="90" r="2"/></g>
</svg>
"""


def _write(tmp_path: Path, gesture: str) -> Path:
    path = tmp_path / "spell_template_test.svg"
    path.write_text(_svg(gesture), encoding="utf-8")
    return path


def test_open_path_loads(tmp_path: Path) -> None:
    svg = _write(tmp_path, '<path d="M10,10 L50,50 L90,90"/>')
    points = load_svg_points(svg)
    assert len(points) == 256


def test_closed_path_rejected(tmp_path: Path) -> None:
    svg = _write(tmp_path, '<path d="M10,10 L50,50 L90,90 Z"/>')
    with pytest.raises(ValueError, match="closed"):
        load_svg_points(svg)


def test_polygon_rejected(tmp_path: Path) -> None:
    svg = _write(tmp_path, '<polygon points="10,10 50,50 90,90"/>')
    with pytest.raises(ValueError, match="closed"):
        load_svg_points(svg)
