"""Reusable widgets and builders for the wand GUI tester.

`ColourPicker` and `PeriodSlider` are QGroupBox subclasses — drop straight into
a layout via `addWidget`. The build_* functions return a QGroupBox (or a
small dataclass when extra handles are needed) and join their buttons into
a shared command `QButtonGroup` so cross-section radio exclusivity holds.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QWidget,
)

from wand.streaming.eliko.pekio_client import Colour

from wand_tester.constants import (
    COLOUR_OPTIONS,
    DEFAULT_BLINK_DUTY_MS,
    DEFAULT_BLINK_PERIOD_MS,
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


class PeriodSlider(QGroupBox):
    """Haptic period slider + spinbox bidirectionally synced. `.value()` returns ms."""

    def __init__(
        self,
        title: str = "Period",
        default_ms: int = DEFAULT_PERIOD_MS,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, parent)
        row = QHBoxLayout(self)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(PERIOD_MIN_MS, PERIOD_MAX_MS)
        self._slider.setSingleStep(PERIOD_STEP_MS)
        self._slider.setPageStep(500)
        self._slider.setTickInterval(1000)
        self._slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._slider.setValue(default_ms)
        self._spin = QSpinBox()
        self._spin.setRange(PERIOD_MIN_MS, PERIOD_MAX_MS)
        self._spin.setSingleStep(PERIOD_STEP_MS)
        self._spin.setValue(default_ms)
        self._spin.setSuffix(" ms")
        # Bidirectional sync — setValue is idempotent so no feedback loop.
        self._slider.valueChanged.connect(self._spin.setValue)
        self._spin.valueChanged.connect(self._slider.setValue)
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


@dataclass
class BlinkGroup:
    """Handles to a blink section's groupbox + custom-mode spinboxes."""

    box: QGroupBox
    period_spin: QSpinBox
    duty_spin: QSpinBox


def build_blink_group(
    button_group: QButtonGroup,
    on_method: Callable[[str], None],
    *,
    title: str = "Blink",
    presets: tuple[tuple[str, str], ...] = (
        ("Fast", "blink_fast"),
        ("Medium", "blink_medium"),
        ("Slow", "blink_slow"),
    ),
    custom_method: str = "blink_custom",
) -> BlinkGroup:
    """Blink section: preset buttons + Custom with period+duty inputs."""
    box = QGroupBox(title)
    row = QHBoxLayout(box)
    for label, method in presets:
        row.addWidget(make_command_button(button_group, label, method, on_method))
    row.addSpacing(16)
    row.addWidget(make_command_button(button_group, "Custom", custom_method, on_method))
    row.addWidget(QLabel("Period (ms):"))
    period_spin = QSpinBox()
    period_spin.setRange(10, 65535)
    period_spin.setSingleStep(50)
    period_spin.setValue(DEFAULT_BLINK_PERIOD_MS)
    row.addWidget(period_spin)
    row.addWidget(QLabel("Duty (ms):"))
    duty_spin = QSpinBox()
    duty_spin.setRange(0, 65535)
    duty_spin.setSingleStep(10)
    duty_spin.setValue(DEFAULT_BLINK_DUTY_MS)
    row.addWidget(duty_spin)
    row.addStretch(1)
    return BlinkGroup(box=box, period_spin=period_spin, duty_spin=duty_spin)
