"""Primer-style info card for a single spell — the left pane of the single-wand
visualiser when the active zone holds exactly one spell.

Dark-theme adaptation of the printed Spells Primer card: title, a
classification·difficulty·pronunciation fact line, nickname, description, the
gesture art, notable uses and source — plus a *computed* CAST DIFFICULTY meter
(1–10, from `spells.spell_difficulty`), distinct from the lore difficulty string.

Zone-driven, not cast-driven: `set_spell` is called from `show_zone`. Lore/art
absent for a spell degrade gracefully (blank lines skipped) — the card is UX-only.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QWidget

from spells.spell_info import SpellInfo
from spells.spell_type import SpellType

_ACCENT = "#c9a227"       # muted gold — Primer deco nod
_MUTED = "#8a8f98"
_DIM = "#3a3a3a"
_FOOTER_LABEL = "#9aa0a9"  # notable-uses / source labels — readable on the dark panel
_FOOTER_BODY = "#c2c7cf"   # notable-uses / source body text
_PARCHMENT = "#f4efe1"    # light inset behind the (black-ink) gesture art
_MAX_RATING = 10
_MARGIN = 26.0


def _rating_colour(rating: float) -> QColor:
    """Spectrum from green (easy, 1) through yellow/orange to red (hard, 10)."""
    frac = max(0.0, min(1.0, (rating - 1.0) / (_MAX_RATING - 1)))
    hue = 120.0 * (1.0 - frac)  # 120° green → 0° red
    return QColor.fromHsvF(hue / 360.0, 0.72, 0.9)


class SpellInfoCard(QWidget):
    """Renders one spell's Primer lore + computed cast difficulty."""

    def __init__(
        self,
        spell_info: dict[SpellType, SpellInfo],
        difficulties: dict[SpellType, float],
        pixmaps: dict[SpellType, QPixmap],
        panel_colour: str,
        text_colour: str,
    ) -> None:
        super().__init__()
        self._spell_info = spell_info
        self._difficulties = difficulties
        self._pixmaps = pixmaps
        self._background = QColor(panel_colour)
        self._text_colour = QColor(text_colour)
        self._spell: SpellType | None = None

    def set_spell(self, spell: SpellType | None) -> None:
        self._spell = spell if spell is not SpellType.NONE else None
        self.update()

    # ── paint ───────────────────────────────────────────────────
    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), self._background)

        w = max(self.width(), 1)
        if self._spell is None:
            self._draw_placeholder(painter, w)
            return

        info = self._spell_info.get(self._spell) or SpellInfo(display_name=self._spell.name.title())
        x = _MARGIN
        content_w = w - 2 * _MARGIN
        y = _MARGIN + 8

        y = self._draw_title(painter, info, x, y, content_w)
        y = self._draw_facts(painter, info, x, y + 10, content_w)
        y = self._draw_nickname(painter, info, x, y + 6, content_w)
        y = self._draw_description(painter, info, x, y + 12, content_w)
        y = self._draw_art(painter, x, y + 10, content_w)
        y = self._draw_difficulty(painter, info, x, y + 16, content_w)
        self._draw_footer(painter, info, x, content_w)

    def _draw_title(self, painter: QPainter, info: SpellInfo, x: float, y: float, w: float) -> float:
        font = QFont("Georgia")  # serif nod to the printed card; Menlo elsewhere
        font.setPointSize(26)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(self._text_colour)
        rect = QRectF(x, y, w, 40)
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, info.display_name.upper())
        bottom = y + 40
        # gold deco rule under the title
        painter.setPen(QColor(_ACCENT))
        painter.drawLine(int(x), int(bottom + 4), int(x + w), int(bottom + 4))
        return bottom + 8

    def _draw_facts(self, painter: QPainter, info: SpellInfo, x: float, y: float, w: float) -> float:
        # Pronunciation first, then classification. Lore difficulty moves to the
        # difficulty block below (labelled "LORE DIFFICULTY").
        facts = " · ".join(f for f in (info.pronunciation, info.classification) if f)
        if not facts:
            return y
        font = QFont("Menlo")
        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(QColor(_MUTED))
        painter.drawText(QRectF(x, y, w, 20), Qt.AlignmentFlag.AlignLeft, facts)
        return y + 20

    def _draw_nickname(self, painter: QPainter, info: SpellInfo, x: float, y: float, w: float) -> float:
        if not info.nickname:
            return y
        font = QFont("Georgia")
        font.setPointSize(13)
        font.setItalic(True)
        painter.setFont(font)
        painter.setPen(QColor(_ACCENT))
        painter.drawText(QRectF(x, y, w, 22), Qt.AlignmentFlag.AlignLeft, f"“{info.nickname}”")
        return y + 22

    def _draw_description(self, painter: QPainter, info: SpellInfo, x: float, y: float, w: float) -> float:
        if not info.description:
            return y
        font = QFont("Menlo")
        font.setPointSize(12)
        font.setItalic(True)
        painter.setFont(font)
        painter.setPen(self._text_colour)
        flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
        bound = painter.boundingRect(QRectF(x, y, w, 200), flags, info.description)
        painter.drawText(bound, flags, info.description)
        return y + bound.height()

    def _draw_art(self, painter: QPainter, x: float, y: float, w: float) -> float:
        # Parchment inset (black-ink glyph on light), echoing the printed card.
        art_h = min(w * 1.08, 360.0)
        panel = QRectF(x, y, w, art_h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(_PARCHMENT))
        painter.drawRoundedRect(panel, 6, 6)

        pixmap = self._pixmaps.get(self._spell) if self._spell is not None else None
        if pixmap is not None and not pixmap.isNull():
            pad = 16.0
            scaled = pixmap.scaled(
                int(w - 2 * pad), int(art_h - 2 * pad),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            px = x + (w - scaled.width()) / 2
            py = y + (art_h - scaled.height()) / 2
            painter.drawPixmap(int(px), int(py), scaled)
        return y + art_h

    def _draw_difficulty(self, painter: QPainter, info: SpellInfo, x: float, y: float, w: float) -> float:
        label_font = QFont("Menlo")
        label_font.setPointSize(11)
        label_font.setBold(True)

        # lore difficulty (Primer's "Beginner / Intermediate / Advanced" string)
        if info.difficulty:
            painter.setFont(label_font)
            painter.setPen(QColor(_MUTED))
            painter.drawText(QRectF(x, y, w, 18), Qt.AlignmentFlag.AlignLeft, "LORE DIFFICULTY")
            value_font = QFont("Menlo")
            value_font.setPointSize(11)
            painter.setFont(value_font)
            painter.setPen(self._text_colour)
            painter.drawText(QRectF(x, y, w, 18), Qt.AlignmentFlag.AlignRight, info.difficulty)
            y += 24

        rating = self._difficulties.get(self._spell) if self._spell is not None else None
        painter.setFont(label_font)
        painter.setPen(QColor(_MUTED))
        painter.drawText(QRectF(x, y, w, 18), Qt.AlignmentFlag.AlignLeft, "CAST DIFFICULTY")

        if rating is None:
            return y + 18

        colour = _rating_colour(rating)
        value_text = f"{rating:.1f} / {_MAX_RATING}"
        painter.setPen(colour)
        painter.drawText(QRectF(x, y, w, 18), Qt.AlignmentFlag.AlignRight, value_text)

        # pip meter: `_MAX_RATING` cells, filled to the rounded rating in the spectrum colour
        meter_y = y + 24
        gap = 6.0
        cell = (w - gap * (_MAX_RATING - 1)) / _MAX_RATING
        filled = int(round(rating))
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(_MAX_RATING):
            cx = x + i * (cell + gap)
            painter.setBrush(colour if i < filled else QColor(_DIM))
            painter.drawRoundedRect(QRectF(cx, meter_y, cell, 10), 2, 2)
        return meter_y + 10

    def _draw_footer(self, painter: QPainter, info: SpellInfo, x: float, w: float) -> None:
        """Notable uses + source, pinned to the bottom of the card."""
        y = self.height() - _MARGIN
        if info.source:
            font = QFont("Menlo")
            font.setPointSize(9)
            font.setItalic(True)
            painter.setFont(font)
            painter.setPen(QColor(_FOOTER_LABEL))
            painter.drawText(QRectF(x, y - 14, w, 14), Qt.AlignmentFlag.AlignLeft, f"SOURCE: {info.source}")
            y -= 20

        if info.notable_uses:
            font = QFont("Menlo")
            font.setPointSize(10)
            painter.setFont(font)
            painter.setPen(QColor(_FOOTER_BODY))
            flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom | Qt.TextFlag.TextWordWrap
            bound = painter.boundingRect(QRectF(x, 0, w, 60), flags, info.notable_uses)
            painter.drawText(QRectF(x, y - bound.height(), w, bound.height()), flags, info.notable_uses)
            y -= bound.height() + 4

            label = QFont("Menlo")
            label.setPointSize(9)
            label.setBold(True)
            painter.setFont(label)
            painter.setPen(QColor(_FOOTER_LABEL))
            painter.drawText(QRectF(x, y - 14, w, 14), Qt.AlignmentFlag.AlignLeft, "NOTABLE USES")

    def _draw_placeholder(self, painter: QPainter, w: int) -> None:
        painter.setPen(QColor("#555"))
        font = QFont("Menlo")
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "no single spell in this zone")
