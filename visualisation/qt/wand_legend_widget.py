from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLayout, QVBoxLayout, QWidget


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


class _LegendRow(QWidget):
    """One wand: swatch · id · zone · targets · last cast, as a single horizontal strip."""

    def __init__(self, wand_id: str, colour: str, zone_id: str, targets: list[str], text_colour: str) -> None:
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self._swatch = _Swatch(QColor(colour))
        self._id = QLabel(wand_id)
        self._zone = QLabel()
        self._targets = QLabel()
        self._last = QLabel()

        self._id.setStyleSheet(f"color: {text_colour}; font-weight: bold;")
        for label in (self._zone, self._targets, self._last):
            label.setStyleSheet(f"color: {text_colour};")
            label.setTextFormat(Qt.TextFormat.RichText)

        self._id.setFixedWidth(64)
        self._zone.setFixedWidth(120)
        self._targets.setMinimumWidth(160)

        row.addWidget(self._swatch)
        row.addWidget(self._id)
        row.addWidget(self._zone)
        row.addWidget(self._targets)
        row.addStretch(1)
        row.addWidget(self._last)

        self.update_fields(colour, zone_id, targets)

    def update_fields(self, colour: str, zone_id: str, targets: list[str]) -> None:
        self._swatch.set_colour(QColor(colour))
        self._zone.setText(zone_id)
        self._targets.setText(", ".join(targets) if targets else "<i>no targets</i>")

    def set_last_cast(self, text: str, colour: str) -> None:
        self._last.setText(f"<span style='color:{colour};'>{text}</span>")


class WandLegendWidget(QFrame):
    """Corner key: one row per active wand. Rows are added on zone-enter and removed on leave,
    so the key always reflects exactly the wands currently drawing trails. Translucent overlay
    child of the canvas; the layout's SetFixedSize keeps the frame hugging its content."""

    def __init__(self, text_colour: str) -> None:
        super().__init__()
        self._text_colour = text_colour
        self._rows: dict[str, _LegendRow] = {}

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("WandLegendWidget { background: rgba(0,0,0,150); border-radius: 8px; }")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 8, 10, 8)
        self._layout.setSpacing(4)
        self._layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self._title = QLabel("Active wands")
        self._title.setStyleSheet(f"color: {text_colour}; font-weight: bold;")
        self._layout.addWidget(self._title)

        self._empty = QLabel("— none —")
        self._empty.setStyleSheet(f"color: {text_colour};")
        self._layout.addWidget(self._empty)

    def upsert(self, wand_id: str, colour: str, zone_id: str, targets: list[str]) -> None:
        row = self._rows.get(wand_id)
        if row is None:
            row = _LegendRow(wand_id, colour, zone_id, targets, self._text_colour)
            self._rows[wand_id] = row
            self._layout.addWidget(row)
        else:
            row.update_fields(colour, zone_id, targets)
        self._empty.setVisible(not self._rows)

    def set_last_cast(self, wand_id: str, text: str, colour: str) -> None:
        row = self._rows.get(wand_id)
        if row is not None:
            row.set_last_cast(text, colour)

    def remove(self, wand_id: str) -> None:
        row = self._rows.pop(wand_id, None)
        if row is None:
            return
        self._layout.removeWidget(row)
        row.hide()  # drop it now; deleteLater only runs on the next event-loop pump
        row.deleteLater()
        self._empty.setVisible(not self._rows)
