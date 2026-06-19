"""LED-only commands tab."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from wand.streaming.eliko.pekio_client import PekioClient

from wand_tester.constants import (
    BLINK_PREFIX,
    BLINK_PRESETS,
    BLINK_PRESETS_BY_NAME,
    DEFAULT_BLINK_DUTY_MS,
    DEFAULT_BLINK_FOR_DURATION_S,
    DEFAULT_BLINK_PERIOD_MS,
    DEFAULT_FADE_FOR_DURATION_S,
    DEFAULT_FADE_STEP,
    FADE_PREFIX,
    FADE_PRESETS,
    FADE_PRESETS_BY_NAME,
)
from wand_tester.styles import AMBER, ROSE, TEAL, VIOLET, group_title_style
from wand_tester.widgets import (
    ColourPicker,
    build_solid_group,
    make_command_button,
)


def _accent(box: QGroupBox, name: str, accent: str) -> QGroupBox:
    """Tag a groupbox with a section colour (title chip + border)."""
    box.setObjectName(name)
    box.setStyleSheet(group_title_style(name, accent))
    return box


class LedTab(QWidget):
    """Solid / Blink / Fade. Blink and Fade each carry a Loop checkbox:
    checked = continuous command (runs until stopped), unchecked = timed
    `*_for` command that auto-stops after the section's Duration. The Duration
    field greys out while Loop is on."""

    def __init__(self, client: PekioClient) -> None:
        super().__init__()
        self._client = client
        self._command_group = QButtonGroup(self)
        self._command_group.setExclusive(True)
        self._selected_method: str = "solid"

        # Last non-timed LED command, re-fired by HapticTab after each haptic
        # CMD1 to restore LED state the wand's firmware just clobbered.
        self._last_led_command: Callable[[], None] | None = None

        self._colour_picker = ColourPicker()

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.addWidget(_accent(self._colour_picker, "ledColour", VIOLET))
        layout.addWidget(_accent(build_solid_group(self._command_group, self._set_method), "ledSolid", TEAL))
        layout.addWidget(self._build_blink_section())
        layout.addWidget(self._build_fade_section())
        layout.addStretch(1)

    def _cmd_btn(self, label: str, method: str) -> QPushButton:
        return make_command_button(self._command_group, label, method, self._set_method)

    def _make_duration_spin(self, default_s: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.1, 600.0)
        spin.setSingleStep(0.5)
        spin.setDecimals(1)
        spin.setValue(default_s)
        return spin

    def _wire_loop(self, loop: QCheckBox, duration_spin: QDoubleSpinBox, duration_label: QLabel) -> None:
        """Duration only applies in timed mode — hide it entirely while Loop is
        on so the section isn't cluttered with a dead field, reveal it on
        un-check."""

        def update(checked: bool) -> None:
            duration_label.setVisible(not checked)
            duration_spin.setVisible(not checked)

        loop.toggled.connect(update)
        update(loop.isChecked())

    def _build_blink_section(self) -> QGroupBox:
        box = _accent(QGroupBox("Blink"), "ledBlink", AMBER)
        outer = QVBoxLayout(box)

        top = QHBoxLayout()
        self._blink_loop = QCheckBox("Loop")
        self._blink_loop.setChecked(True)
        top.addWidget(self._blink_loop)
        top.addSpacing(8)
        for label, _p, _d in BLINK_PRESETS:
            top.addWidget(self._cmd_btn(label, f"{BLINK_PREFIX}:{label}"))
        top.addStretch(1)
        self._blink_duration_label = QLabel("Duration (s):")
        top.addWidget(self._blink_duration_label)
        self._blink_duration_spin = self._make_duration_spin(DEFAULT_BLINK_FOR_DURATION_S)
        top.addWidget(self._blink_duration_spin)
        outer.addLayout(top)

        # Custom button + the inputs it controls, grouped together.
        custom = QHBoxLayout()
        custom.addWidget(self._cmd_btn("Custom", "blink_custom"))
        custom.addWidget(QLabel("Period (ms):"))
        self._blink_period_spin = QSpinBox()
        self._blink_period_spin.setRange(10, 65535)
        self._blink_period_spin.setSingleStep(50)
        self._blink_period_spin.setValue(DEFAULT_BLINK_PERIOD_MS)
        custom.addWidget(self._blink_period_spin)
        custom.addWidget(QLabel("Duty (ms):"))
        self._blink_duty_spin = QSpinBox()
        self._blink_duty_spin.setRange(0, 65535)
        self._blink_duty_spin.setSingleStep(10)
        self._blink_duty_spin.setValue(DEFAULT_BLINK_DUTY_MS)
        custom.addWidget(self._blink_duty_spin)
        custom.addStretch(1)
        outer.addLayout(custom)

        self._wire_loop(self._blink_loop, self._blink_duration_spin, self._blink_duration_label)
        return box

    def _build_fade_section(self) -> QGroupBox:
        box = _accent(QGroupBox("Fade"), "ledFade", ROSE)
        outer = QVBoxLayout(box)

        top = QHBoxLayout()
        self._fade_loop = QCheckBox("Loop")
        self._fade_loop.setChecked(True)
        top.addWidget(self._fade_loop)
        top.addSpacing(8)
        for label, _step in FADE_PRESETS:
            top.addWidget(self._cmd_btn(label, f"{FADE_PREFIX}:{label}"))
        top.addStretch(1)
        self._fade_duration_label = QLabel("Duration (s):")
        top.addWidget(self._fade_duration_label)
        self._fade_duration_spin = self._make_duration_spin(DEFAULT_FADE_FOR_DURATION_S)
        top.addWidget(self._fade_duration_spin)
        outer.addLayout(top)

        # Custom button + the input it controls, grouped together.
        custom = QHBoxLayout()
        custom.addWidget(self._cmd_btn("Custom", "fade_custom"))
        custom.addWidget(QLabel("Step:"))
        self._fade_step_spin = QSpinBox()
        self._fade_step_spin.setRange(1, 255)
        self._fade_step_spin.setValue(DEFAULT_FADE_STEP)
        custom.addWidget(self._fade_step_spin)
        custom.addStretch(1)
        outer.addLayout(custom)

        self._wire_loop(self._fade_loop, self._fade_duration_spin, self._fade_duration_label)
        return box

    def emergency_stop(self) -> None:
        """Called by the top-level Stop button. LED tab has no widget-local
        timers — the client's _cancel_pending_stop (invoked by client.stop_all)
        handles the timed `*_for` auto-stops. Also drops the reapply lambda so
        the next haptic tick doesn't resurrect what Stop just killed."""
        self._last_led_command = None

    def _set_method(self, method: str) -> None:
        self._selected_method = method

    @staticmethod
    def _is_blink(method: str) -> bool:
        return method == "blink_custom" or method.startswith(f"{BLINK_PREFIX}:")

    @staticmethod
    def _is_fade(method: str) -> bool:
        return method == "fade_custom" or method.startswith(f"{FADE_PREFIX}:")

    def send(self) -> None:
        method = self._selected_method
        colour = self._colour_picker.selected
        cmd: Callable[[], None]
        timed = False

        if self._is_blink(method):
            if method == "blink_custom":
                period, duty = self._blink_period_spin.value(), self._blink_duty_spin.value()
            else:
                period, duty = BLINK_PRESETS_BY_NAME[method.split(":", 1)[1]]
            if duty >= period:
                print(f"[invalid] blink duty ({duty}) must be < period ({period})")
                return
            if self._blink_loop.isChecked():
                cmd = lambda: self._client.blink(period, duty, colour)
            else:
                duration = self._blink_duration_spin.value()
                cmd = lambda: self._client.blink_for(duration, period, duty, colour)
                timed = True
        elif self._is_fade(method):
            if method == "fade_custom":
                step = self._fade_step_spin.value()
            else:
                step = FADE_PRESETS_BY_NAME[method.split(":", 1)[1]]
            if self._fade_loop.isChecked():
                cmd = lambda: self._client.fade(step, colour)
            else:
                duration = self._fade_duration_spin.value()
                cmd = lambda: self._client.fade_for(duration, step, colour)
                timed = True
        else:  # solid
            cmd = lambda: self._client.solid(colour)

        cmd()
        # Timed commands re-arm their own duration on re-fire, so drop them
        # from reapply rather than chaining a Stop-All flurry.
        self._last_led_command = None if timed else cmd

    def reapply_last(self) -> None:
        """Re-issue the most recent non-timed LED command. Called by HapticTab
        after each haptic CMD1 to restore LED state on this firmware."""
        if self._last_led_command is not None:
            self._last_led_command()
