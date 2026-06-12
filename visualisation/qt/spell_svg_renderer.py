"""Render a layered spell SVG to a QPixmap for the UI target image.

Replaces the per-spell PNGs: one layered SVG is the single source of truth for
both recognizer geometry (see svg_template_loader) and this UI art. Crisp at any
resolution, no PNG maintenance.

All three layers are drawn: `gesture`, `arrows`, and the `origin` marker (so the
cast start is visible). Template ink is forced to black and drawn on a white
background so it always reads clearly regardless of the source SVG colours.
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from spells.spell_type import SpellType

# Any explicit hex colour -> black. `fill:none` (no hex) is left untouched, so
# the gesture stroke stays an outline rather than a filled blob.
_HEX_COLOUR = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")


def _svg_black(svg_path: Path) -> bytes:
    """SVG bytes with every explicit colour recoloured black."""
    text = svg_path.read_text(encoding="utf-8")
    return _HEX_COLOUR.sub("#000", text).encode("utf-8")


def render_spell_pixmap(svg_path: Path, size: int, bg_colour: str | None = None) -> QPixmap:
    """Render a spell SVG (black ink) into a `size`x`size` QPixmap.

    `bg_colour` fills the background; None leaves it transparent. The SVG is
    aspect-fit and centred (templates use a square 300x300 viewBox).
    """
    renderer = QSvgRenderer(QByteArray(_svg_black(svg_path)))

    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(bg_colour) if bg_colour else Qt.GlobalColor.transparent)

    default = renderer.defaultSize()
    if default.width() > 0 and default.height() > 0:
        scale = min(size / default.width(), size / default.height())
        w = default.width() * scale
        h = default.height() * scale
        target = QRectF((size - w) / 2, (size - h) / 2, w, h)
    else:
        target = QRectF(0, 0, size, size)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter, target)
    painter.end()
    return pixmap


def render_spell_library(templates_dir: Path, size: int, bg_colour: str | None = None) -> dict[SpellType, QPixmap]:
    """Render every SpellType that has a `<name>.svg` template into a QPixmap."""
    out: dict[SpellType, QPixmap] = {}
    for spell in SpellType:
        if spell is SpellType.NONE:
            continue
        svg = templates_dir / f"{spell.name.lower()}.svg"
        if svg.exists():
            out[spell] = render_spell_pixmap(svg, size, bg_colour)
    return out
