from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QWidget


class _Swatch(QLabel):
    """Solid colour chip for the id->colour key."""

    def __init__(self, colour: QColor) -> None:
        super().__init__()
        self._colour = colour
        self.setFixedSize(14, 14)

    def set_colour(self, colour: QColor) -> None:
        self._colour = colour
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._colour)
        painter.drawRoundedRect(self.rect(), 3, 3)


class _LegendRow:
    def __init__(self, grid: QGridLayout, row: int, colour: QColor, text_colour: str) -> None:
        self.swatch = _Swatch(colour)
        self.id = QLabel()
        self.zone = QLabel()
        self.targets = QLabel()
        self.last_cast = QLabel()

        self.id.setStyleSheet(f"color: {text_colour}; font-weight: bold;")
        for label in (self.zone, self.targets, self.last_cast):
            label.setStyleSheet(f"color: {text_colour};")
            label.setTextFormat(Qt.TextFormat.RichText)

        grid.addWidget(self.swatch, row, 0, Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self.id, row, 1)
        grid.addWidget(self.zone, row, 2)
        grid.addWidget(self.targets, row, 3)
        grid.addWidget(self.last_cast, row, 4)

    def widgets(self) -> list[QWidget]:
        return [self.swatch, self.id, self.zone, self.targets, self.last_cast]


class WandLegendWidget(QFrame):
    """Corner key: one row per active wand — colour swatch · id · zone · spell targets · last cast.

    Rows are added on zone-enter and removed on leave, so the key always reflects exactly the
    wands currently drawing trails. Designed as a translucent overlay child of the canvas."""

    def __init__(self, text_colour: str) -> None:
        super().__init__()
        self._text_colour = text_colour
        self._rows: dict[str, _LegendRow] = {}

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("WandLegendWidget { background: rgba(0,0,0,140); border-radius: 8px; }")

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(10, 8, 10, 8)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(4)

        self._title = QLabel("Active wands")
        self._title.setStyleSheet(f"color: {text_colour}; font-weight: bold;")
        self._grid.addWidget(self._title, 0, 0, 1, 5)

        self._empty = QLabel("— none —")
        self._empty.setStyleSheet(f"color: {text_colour};")
        self._grid.addWidget(self._empty, 1, 0, 1, 5)

    def upsert(self, wand_id: str, colour: str, zone_id: str, targets: list[str]) -> None:
        row = self._rows.get(wand_id)
        if row is None:
            row = _LegendRow(self._grid, len(self._rows) + 2, QColor(colour), self._text_colour)
            self._rows[wand_id] = row
            row.last_cast.setText("")
        row.swatch.set_colour(QColor(colour))
        row.id.setText(wand_id)
        row.zone.setText(zone_id)
        row.targets.setText(", ".join(targets) if targets else "<i>no targets</i>")
        self._refresh()

    def set_last_cast(self, wand_id: str, text: str, colour: str) -> None:
        row = self._rows.get(wand_id)
        if row is None:
            return
        row.last_cast.setText(f"<span style='color:{colour};'>{text}</span>")
        self._refresh()

    def remove(self, wand_id: str) -> None:
        row = self._rows.pop(wand_id, None)
        if row is None:
            return
        for widget in row.widgets():
            self._grid.removeWidget(widget)
            widget.deleteLater()
        self._reflow()
        self._refresh()

    def _reflow(self) -> None:
        """Re-pack remaining rows into contiguous grid rows after a removal."""
        for i, row in enumerate(self._rows.values()):
            for col, widget in enumerate(row.widgets()):
                self._grid.addWidget(widget, i + 2, col)

    def _refresh(self) -> None:
        self._empty.setVisible(not self._rows)
        self.adjustSize()
