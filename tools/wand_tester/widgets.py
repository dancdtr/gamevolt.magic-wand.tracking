"""Reusable widgets and builders for the wand GUI tester.

`ColourPicker` and `PeriodSlider` are QGroupBox subclasses — drop straight into
a layout via `addWidget`. The build_* functions return a QGroupBox and join
their buttons into a shared command `QButtonGroup` so cross-section radio
exclusivity holds.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)

from wand.streaming.eliko.pekio_client import Colour

from wand_tester.constants import (
    COLOUR_OPTIONS,
    DEFAULT_COLOUR,
    DEFAULT_PERIOD_MS,
    PERIOD_MAX_MS,
    PERIOD_MIN_MS,
    PERIOD_STEP_MS,
)
from wand_tester.styles import (
    colour_button_style,
    command_button_style,
)


class ColourPicker(QGroupBox):
    """4-column LED colour grid. Tabs read `.selected` at Send time."""

    def __init__(self, default_name: str = DEFAULT_COLOUR, parent: QWidget | None = None) -> None:
        super().__init__("Colour", parent)
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self.selected: Colour = Colour.RED

        grid = QGridLayout(self)
        cols = 4
        for idx, opt in enumerate(COLOUR_OPTIONS):
            btn = QPushButton(opt.name)
            btn.setCheckable(True)
            btn.setStyleSheet(colour_button_style(opt.bg, opt.fg))
            if opt.name == default_name:
                btn.setChecked(True)
                self.selected = opt.colour
            self._button_group.addButton(btn, idx)
            btn.toggled.connect(lambda checked, c=opt.colour: checked and self._set(c))
            grid.addWidget(btn, idx // cols, idx % cols)

    def _set(self, colour: Colour) -> None:
        self.selected = colour


class PeriodSlider(QWidget):
    """Compact single-row interval control: a label, a slider, and a seconds
    spinbox bidirectionally synced. Displays seconds; `.value()` returns ms so
    callers keep their ms granularity."""

    def __init__(
        self,
        title: str = "Repeat every",
        default_ms: int = DEFAULT_PERIOD_MS,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QLabel(f"{title}:"))
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(PERIOD_MIN_MS, PERIOD_MAX_MS)
        self._slider.setSingleStep(PERIOD_STEP_MS)
        self._slider.setPageStep(500)
        self._slider.setValue(default_ms)
        self._slider.setMaximumWidth(220)
        self._spin = QDoubleSpinBox()
        self._spin.setRange(PERIOD_MIN_MS / 1000, PERIOD_MAX_MS / 1000)
        self._spin.setSingleStep(PERIOD_STEP_MS / 1000)
        self._spin.setDecimals(2)
        self._spin.setSuffix(" s")
        self._spin.setValue(default_ms / 1000)
        # Bidirectional sync — setValue is idempotent so no feedback loop.
        self._slider.valueChanged.connect(lambda ms: self._spin.setValue(ms / 1000))
        self._spin.valueChanged.connect(lambda s: self._slider.setValue(int(round(s * 1000))))
        row.addWidget(self._slider, 1)
        row.addWidget(self._spin)

    def value(self) -> int:
        return self._slider.value()


def make_command_button(
    button_group: QButtonGroup,
    label: str,
    method: str,
    on_method: Callable[[str], None],
) -> QPushButton:
    """Checkable command button registered into button_group; fires
    on_method(method) when toggled on."""
    btn = QPushButton(label)
    btn.setCheckable(True)
    btn.setStyleSheet(command_button_style())
    button_group.addButton(btn)
    btn.toggled.connect(lambda checked, m=method: checked and on_method(m))
    return btn


def build_solid_group(
    button_group: QButtonGroup,
    on_method: Callable[[str], None],
    *,
    method: str = "solid",
    initial_checked: bool = True,
) -> QGroupBox:
    """Single-button Solid group joined to a shared command button_group."""
    box = QGroupBox("Solid")
    row = QHBoxLayout(box)
    btn = make_command_button(button_group, "Solid", method, on_method)
    if initial_checked:
        btn.setChecked(True)
    row.addWidget(btn)
    row.addStretch(1)
    return box
