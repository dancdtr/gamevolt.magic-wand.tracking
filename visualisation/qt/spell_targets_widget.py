from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from spells.spell_type import SpellType

_FLASH_MS = 450


class SpellTargetsWidget(QWidget):
    """Shows the active zone's spell targets, tiled to fit. On a cast the matched
    spell's tile flashes the quality colour (red when rejected)."""

    def __init__(self, pixmaps: dict[SpellType, QPixmap], background: str, text_colour: str) -> None:
        super().__init__()
        self._pixmaps = pixmaps
        self._background = QColor(background)
        self._text_colour = QColor(text_colour)

        self._spells: list[SpellType] = []
        self._flash_spell: SpellType | None = None
        self._flash_colour: QColor | None = None

        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._clear_flash)

    def set_spells(self, spells: list[SpellType]) -> None:
        self._spells = [s for s in spells if s is not SpellType.NONE]
        self._clear_flash()
        self.update()

    def flash(self, spell: SpellType, colour: str) -> None:
        self._flash_spell = spell
        self._flash_colour = QColor(colour)
        self._flash_timer.start(_FLASH_MS)
        self.update()

    def _clear_flash(self) -> None:
        self._flash_spell = None
        self._flash_colour = None
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), self._background)

        w = max(self.width(), 1)
        h = max(self.height(), 1)

        if not self._spells:
            painter.setPen(QColor("#555"))
            font = QFont("Menlo")
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "no active zone")
            return

        n = len(self._spells)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        cell_w = w / cols
        cell_h = h / rows

        for i, spell in enumerate(self._spells):
            r, c = divmod(i, cols)
            cell = QRectF(c * cell_w, r * cell_h, cell_w, cell_h)
            self._draw_cell(painter, spell, cell)

    def _draw_cell(self, painter: QPainter, spell: SpellType, cell: QRectF) -> None:
        margin = 14
        inner = cell.adjusted(margin, margin, -margin, -margin)

        pixmap = self._pixmaps.get(spell)
        if pixmap is not None and not pixmap.isNull():
            scaled = pixmap.scaled(
                int(inner.width()),
                int(max(inner.height() - 22, 1)),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            px = inner.x() + (inner.width() - scaled.width()) / 2
            py = inner.y() + (inner.height() - 22 - scaled.height()) / 2
            painter.drawPixmap(int(px), int(py), scaled)

        # label
        painter.setPen(self._text_colour)
        font = QFont("Menlo")
        font.setPointSize(11)
        painter.setFont(font)
        label_rect = QRectF(cell.x(), cell.bottom() - 24, cell.width(), 20)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, spell.name)

        # flash overlay on the matched tile
        if spell is self._flash_spell and self._flash_colour is not None:
            tint = QColor(self._flash_colour)
            tint.setAlpha(60)
            painter.fillRect(cell, tint)
            pen = QPen(self._flash_colour)
            pen.setWidth(5)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(cell.adjusted(3, 3, -3, -3))
