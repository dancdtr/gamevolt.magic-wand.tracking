"""Haptic-only commands tab."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from wand.streaming.eliko.pekio_client import BUZZ_PATTERN_1, PekioClient

from wand_tester.constants import (
    HAPTIC_MODE_ALARM,
    HAPTIC_MODE_ONESHOT,
    HAPTIC_MODE_SEQUENCE,
    HAPTIC_PATTERNS,
)
from wand_tester.styles import (
    action_button_style,
    preset_button_style,
)
from wand_tester.widgets import (
    PeriodSlider,
    make_command_button,
)


class HapticTab(QWidget):
    """Haptic-only commands: one-shot waveform, repeating sequence, periodic buzz.

    Mode (exclusive radio) picks which client method fires on Send.
        One-shot → hwave_oneshot(*waveforms)
        Sequence → buzz_hwave-like loop using hwave_oneshot
        Alarm    → buzz(period_ms)
    """

    def __init__(
        self,
        client: PekioClient,
        restore_led: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._client = client
        # Every haptic CMD1 clobbers LED state (firmware bundles them). Call
        # this after each haptic CMD1 to re-issue the user's last LED command.
        # Not used for Alarm mode — re-firing LED would overwrite firmware's
        # periodic buzz state and silence the alarm.
        self._restore_led = restore_led
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._mode: str = HAPTIC_MODE_ONESHOT

        # Sequence mode drives a Qt-main-thread loop of hwave_oneshot — avoids
        # the buzz_hwave Timer-thread + dedupe-breaker path which the firmware
        # handles unreliably. Snapshot of waveforms taken at Send time.
        self._sequence_waveforms: tuple[int, ...] = ()
        self._sequence_timer = QTimer(self)
        self._sequence_timer.timeout.connect(self._fire_sequence_tick)

        self._period = PeriodSlider("Period")

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_mode_group())
        layout.addWidget(self._build_sequence_group())
        layout.addWidget(self._period)
        layout.addLayout(self._build_action_row())
        layout.addStretch(1)

    def _build_mode_group(self) -> QGroupBox:
        box = QGroupBox("Mode")
        row = QHBoxLayout(box)
        for label, mode in [
            ("One-shot", HAPTIC_MODE_ONESHOT),
            ("Sequence", HAPTIC_MODE_SEQUENCE),
            ("Alarm", HAPTIC_MODE_ALARM),
        ]:
            btn = make_command_button(self._mode_group, label, mode, self._set_mode)
            if mode == HAPTIC_MODE_ONESHOT:
                btn.setChecked(True)
            row.addWidget(btn)
        row.addStretch(1)
        return box

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        # Switching modes cancels any active sequence loop.
        self._sequence_timer.stop()

    def _build_sequence_group(self) -> QGroupBox:
        box = QGroupBox("Sequence")
        layout = QVBoxLayout(box)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset:"))
        for label, pattern in HAPTIC_PATTERNS:
            btn = QPushButton(label)
            btn.setStyleSheet(preset_button_style())
            btn.setToolTip(f"Waveforms: {', '.join(str(w) for w in pattern)}")
            btn.clicked.connect(lambda _checked=False, p=pattern: self._fill_waveforms(p))
            preset_row.addWidget(btn)
        preset_row.addStretch(1)
        layout.addLayout(preset_row)

        spin_row = QHBoxLayout()
        spin_row.addWidget(QLabel("Waveform 1:"))
        self._w1_spin = self._make_waveform_spin(BUZZ_PATTERN_1[0])
        spin_row.addWidget(self._w1_spin)
        spin_row.addWidget(QLabel("Waveform 2:"))
        self._w2_spin = self._make_waveform_spin(BUZZ_PATTERN_1[1])
        spin_row.addWidget(self._w2_spin)
        spin_row.addWidget(QLabel("Waveform 3:"))
        self._w3_spin = self._make_waveform_spin(BUZZ_PATTERN_1[2])
        spin_row.addWidget(self._w3_spin)
        spin_row.addWidget(QLabel("(0 = unused)"))
        spin_row.addStretch(1)
        layout.addLayout(spin_row)
        return box

    def _make_waveform_spin(self, default: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 255)
        spin.setValue(default)
        return spin

    def _fill_waveforms(self, pattern: tuple[int, ...]) -> None:
        self._w1_spin.setValue(pattern[0] if len(pattern) > 0 else 0)
        self._w2_spin.setValue(pattern[1] if len(pattern) > 1 else 0)
        self._w3_spin.setValue(pattern[2] if len(pattern) > 2 else 0)

    def _build_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addStretch(1)
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(action_button_style("#208040"))
        send_btn.clicked.connect(self._on_send)
        row.addWidget(send_btn)
        return row

    def _waveforms(self) -> list[int]:
        return [w for w in (self._w1_spin.value(), self._w2_spin.value(), self._w3_spin.value()) if w > 0]

    def _fire_sequence_tick(self) -> None:
        period_ms = self._period.value()
        # Clear must fire before next tick or the dedupe breaker re-engages.
        clear_delay_s = (period_ms / 1000.0) / 2.0
        self._client.hwave_oneshot(*self._sequence_waveforms, clear_delay_s=clear_delay_s)
        if self._restore_led is not None:
            self._restore_led()

    def _on_send(self) -> None:
        # Any Send cancels a running sequence loop — caller picks a new command.
        self._sequence_timer.stop()
        if self._mode == HAPTIC_MODE_ONESHOT:
            waveforms = self._waveforms()
            if not waveforms:
                print("[invalid] one-shot requires at least one waveform > 0")
                return
            self._client.hwave_oneshot(*waveforms)
            if self._restore_led is not None:
                self._restore_led()
        elif self._mode == HAPTIC_MODE_SEQUENCE:
            waveforms = self._waveforms()
            if not waveforms:
                print("[invalid] sequence requires at least one waveform > 0")
                return
            period_ms = self._period.value()
            self._sequence_waveforms = tuple(waveforms)
            self._fire_sequence_tick()
            self._sequence_timer.start(period_ms)
        elif self._mode == HAPTIC_MODE_ALARM:
            # No LED restore: would overwrite firmware-managed periodic buzz
            # state and kill the alarm. Use LED+Haptic tab to combine.
            self._client.buzz(self._period.value())

    def emergency_stop(self) -> None:
        """Called by top-level Stop All. Cancels the local sequence-loop timer
        so the next click of Send starts fresh."""
        self._sequence_timer.stop()
