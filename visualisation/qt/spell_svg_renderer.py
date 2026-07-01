"""Render a layered spell SVG to a QPixmap for the UI target image.

Replaces the per-spell PNGs: one layered SVG is the single source of truth for
both recognizer geometry (see svg_template_loader) and this UI art. Crisp at any
resolution, no PNG maintenance.

The user-facing target image draws the prettied `gesture_visual` stroke plus the
`mid_arrows`, `origin` and `end_arrow` markers. The `gesture_path` centreline (a
duplicate of the visual, meant only for the recognizer) and the `bg` editor
backdrop are hidden. Template ink is forced to black on a white background so it
always reads clearly regardless of the source SVG colours.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from spells.spell_type import SpellType

# Template files are named `spell_template_<spell_name>.svg` (see template_library).
_FILENAME_PREFIX = "spell_template_"

# Layer ids never drawn in the UI: the recognizer-only centreline and the
# editor-only dark backdrop.
_UI_HIDDEN_LAYERS = frozenset({"gesture_path", "bg"})

_SVG_NS = "http://www.w3.org/2000/svg"

# Any explicit hex colour -> black. `fill:none` (no hex) is left untouched, so
# the gesture stroke stays an outline rather than a filled blob.
_HEX_COLOUR = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")


def _local(tag: str) -> str:
    """Strip XML namespace: '{http://...}g' -> 'g'."""
    return tag.rsplit("}", 1)[-1]


def _svg_black(svg_path: Path, hidden_layers: frozenset[str]) -> bytes:
    """SVG bytes with `hidden_layers` groups removed and every colour recoloured black."""
    ET.register_namespace("", _SVG_NS)  # serialise <g>, not <ns0:g>
    root = ET.parse(str(svg_path)).getroot()

    for group in [el for el in root if _local(el.tag) == "g" and (el.get("id") or "").lower() in hidden_layers]:
        root.remove(group)

    text = ET.tostring(root, encoding="unicode")
    return _HEX_COLOUR.sub("#000", text).encode("utf-8")


def render_spell_pixmap(
    svg_path: Path,
    size: int,
    bg_colour: str | None = None,
    hidden_layers: frozenset[str] = _UI_HIDDEN_LAYERS,
) -> QPixmap:
    """Render a spell SVG (black ink) into a `size`x`size` QPixmap.

    `bg_colour` fills the background; None leaves it transparent. `hidden_layers`
    are dropped before rendering. The SVG is aspect-fit and centred.
    """
    renderer = QSvgRenderer(QByteArray(_svg_black(svg_path, hidden_layers)))

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
    """Render every SpellType with a `spell_template_<name>.svg` template into a QPixmap."""
    out: dict[SpellType, QPixmap] = {}
    for spell in SpellType:
        if spell is SpellType.NONE:
            continue
        svg = templates_dir / f"{_FILENAME_PREFIX}{spell.name.lower()}.svg"
        if svg.exists():
            out[spell] = render_spell_pixmap(svg, size, bg_colour)
    return out
