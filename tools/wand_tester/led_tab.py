"""LED-only commands tab."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QButtonGroup,
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
    DEFAULT_BLINK_DUTY_MS,
    DEFAULT_BLINK_FOR_DURATION_S,
    DEFAULT_BLINK_PERIOD_MS,
    DEFAULT_FADE_FOR_DURATION_S,
    DEFAULT_FADE_STEP,
    LED_TIMED_METHODS,
)
from wand_tester.styles import action_button_style
from wand_tester.widgets import (
    ColorPicker,
    build_blink_group,
    build_solid_group,
    make_command_button,
)


class LedTab(QWidget):
    def __init__(self, client: PekioClient) -> None:
        super().__init__()
        self._client = client
        self._command_group = QButtonGroup(self)
        self._command_group.setExclusive(True)
        self._selected_method: str = "solid"

        # Last non-timed LED command, re-fired by HapticTab after each haptic
        # CMD1 to restore LED state the wand's firmware just clobbered.
        self._last_led_command: Callable[[], None] | None = None

        self._color_picker = ColorPicker()
        blink = build_blink_group(self._command_group, self._set_method)
        self._blink_period_spin = blink.period_spin
        self._blink_duty_spin = blink.duty_spin

        layout = QVBoxLayout(self)
        layout.addWidget(self._color_picker)
        layout.addWidget(build_solid_group(self._command_group, self._set_method))
        layout.addWidget(blink.box)
        layout.addWidget(self._build_fade_group())
        layout.addWidget(self._build_timed_group())
        layout.addLayout(self._build_action_row())
        layout.addStretch(1)

    def _cmd_btn(self, label: str, method: str) -> QPushButton:
        return make_command_button(self._command_group, label, method, self._set_method)

    def _build_fade_group(self) -> QGroupBox:
        box = QGroupBox("Fade")
        row = QHBoxLayout(box)
        row.addWidget(self._cmd_btn("Slow", "fade_slow"))
        row.addWidget(self._cmd_btn("Medium", "fade_medium"))
        row.addWidget(self._cmd_btn("Fast", "fade_fast"))
        row.addSpacing(16)
        row.addWidget(self._cmd_btn("Custom", "fade_custom"))
        row.addWidget(QLabel("Step:"))
        self._fade_step_spin = QSpinBox()
        self._fade_step_spin.setRange(1, 255)
        self._fade_step_spin.setValue(DEFAULT_FADE_STEP)
        row.addWidget(self._fade_step_spin)
        row.addStretch(1)
        return box

    def _make_duration_spin(self, default_s: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.1, 600.0)
        spin.setSingleStep(0.5)
        spin.setDecimals(1)
        spin.setValue(default_s)
        return spin

    def _build_timed_group(self) -> QGroupBox:
        box = QGroupBox("Timed (auto-stop)")
        layout = QVBoxLayout(box)
        layout.addWidget(self._build_blink_for_group())
        layout.addWidget(self._build_fade_for_group())
        return box

    def _build_blink_for_group(self) -> QGroupBox:
        box = QGroupBox("Blink")
        row = QHBoxLayout(box)
        row.addWidget(self._cmd_btn("Fast", "blink_fast_for"))
        row.addWidget(self._cmd_btn("Medium", "blink_medium_for"))
        row.addWidget(self._cmd_btn("Slow", "blink_slow_for"))
        row.addSpacing(12)
        row.addWidget(QLabel("Duration (s):"))
        self._blink_for_duration_spin = self._make_duration_spin(DEFAULT_BLINK_FOR_DURATION_S)
        row.addWidget(self._blink_for_duration_spin)
        row.addSpacing(12)
        row.addWidget(self._cmd_btn("Custom", "blink_for_custom"))
        row.addWidget(QLabel("Period (ms):"))
        self._blink_for_period_spin = QSpinBox()
        self._blink_for_period_spin.setRange(10, 65535)
        self._blink_for_period_spin.setSingleStep(50)
        self._blink_for_period_spin.setValue(DEFAULT_BLINK_PERIOD_MS)
        row.addWidget(self._blink_for_period_spin)
        row.addWidget(QLabel("Duty (ms):"))
        self._blink_for_duty_spin = QSpinBox()
        self._blink_for_duty_spin.setRange(0, 65535)
        self._blink_for_duty_spin.setSingleStep(10)
        self._blink_for_duty_spin.setValue(DEFAULT_BLINK_DUTY_MS)
        row.addWidget(self._blink_for_duty_spin)
        row.addStretch(1)
        return box

    def _build_fade_for_group(self) -> QGroupBox:
        box = QGroupBox("Fade")
        row = QHBoxLayout(box)
        row.addWidget(self._cmd_btn("Slow", "fade_slow_for"))
        row.addWidget(self._cmd_btn("Medium", "fade_medium_for"))
        row.addWidget(self._cmd_btn("Fast", "fade_fast_for"))
        row.addSpacing(12)
        row.addWidget(QLabel("Duration (s):"))
        self._fade_for_duration_spin = self._make_duration_spin(DEFAULT_FADE_FOR_DURATION_S)
        row.addWidget(self._fade_for_duration_spin)
        row.addSpacing(12)
        row.addWidget(self._cmd_btn("Custom", "fade_for_custom"))
        row.addWidget(QLabel("Step:"))
        self._fade_for_step_spin = QSpinBox()
        self._fade_for_step_spin.setRange(1, 255)
        self._fade_for_step_spin.setValue(DEFAULT_FADE_STEP)
        row.addWidget(self._fade_for_step_spin)
        row.addStretch(1)
        return box

    def _build_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addStretch(1)
        stop_btn = QPushButton("Stop LED")
        stop_btn.setStyleSheet(action_button_style("#d97718"))
        stop_btn.clicked.connect(self._on_stop)
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(action_button_style("#208040"))
        send_btn.clicked.connect(self._on_send)
        row.addWidget(stop_btn)
        row.addWidget(send_btn)
        return row

    def emergency_stop(self) -> None:
        """Called by top-level Stop All. LED tab has no widget-local timers —
        the client's _cancel_pending_stop (invoked by client.stop_all) handles
        the pulse/*_for auto-stops. Also drops the reapply lambda so the next
        haptic tick doesn't resurrect what Stop All just killed."""
        self._last_led_command = None

    def _set_method(self, method: str) -> None:
        self._selected_method = method

    def _on_send(self) -> None:
        method = self._selected_method
        color = self._color_picker.selected
        cmd: Callable[[], None]
        if method == "blink_custom":
            period = self._blink_period_spin.value()
            duty = self._blink_duty_spin.value()
            if duty >= period:
                print(f"[invalid] blink duty ({duty}) must be < period ({period})")
                return
            cmd = lambda: self._client.blink(period, duty, color)
        elif method == "fade_custom":
            step = self._fade_step_spin.value()
            cmd = lambda: self._client.fade(step, color)
        elif method == "blink_for_custom":
            duration = self._blink_for_duration_spin.value()
            period = self._blink_for_period_spin.value()
            duty = self._blink_for_duty_spin.value()
            if duty >= period:
                print(f"[invalid] blink duty ({duty}) must be < period ({period})")
                return
            cmd = lambda: self._client.blink_for(duration, period, duty, color)
        elif method in ("blink_fast_for", "blink_medium_for", "blink_slow_for"):
            duration = self._blink_for_duration_spin.value()
            cmd = lambda m=method, d=duration: getattr(self._client, m)(d, color)
        elif method == "fade_for_custom":
            duration = self._fade_for_duration_spin.value()
            step = self._fade_for_step_spin.value()
            cmd = lambda: self._client.fade_for(duration, step, color)
        elif method in ("fade_slow_for", "fade_medium_for", "fade_fast_for"):
            duration = self._fade_for_duration_spin.value()
            cmd = lambda m=method, d=duration: getattr(self._client, m)(d, color)
        else:
            cmd = lambda m=method: getattr(self._client, m)(color)
        cmd()
        # Timed commands re-arm their own duration on re-fire, so drop them
        # from reapply rather than chaining a Stop-All flurry.
        self._last_led_command = None if method in LED_TIMED_METHODS else cmd

    def reapply_last(self) -> None:
        """Re-issue the most recent non-timed LED command. Called by HapticTab
        after each haptic CMD1 to restore LED state on this firmware."""
        if self._last_led_command is not None:
            self._last_led_command()

    def _on_stop(self) -> None:
        self._last_led_command = None
        self._client.stop_led()
