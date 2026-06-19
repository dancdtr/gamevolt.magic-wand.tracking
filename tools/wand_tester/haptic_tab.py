"""Haptic-only commands tab."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from wand.streaming.eliko.pekio_client import BUZZ_PATTERN_1, PekioClient

from wand_tester.constants import HAPTIC_EFFECTS
from wand_tester.styles import TEAL, group_title_style, preset_button_style
from wand_tester.widgets import PeriodSlider


class HapticTab(QWidget):
    """Haptic-only commands. A Loop checkbox mirrors the LED tab:
        unchecked → hwave_oneshot(*waveforms) once
        checked   → repeats it every "Repeat every" interval (Qt-main-thread
                    loop of hwave_oneshot, which the firmware handles more
                    reliably than the buzz_hwave Timer-thread path).
    The Repeat-interval control shows only while Loop is on.
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
        self._restore_led = restore_led

        # Snapshot of waveforms taken at Send time, replayed each loop tick.
        self._sequence_waveforms: tuple[int, ...] = ()
        self._sequence_timer = QTimer(self)
        self._sequence_timer.timeout.connect(self._fire_sequence_tick)

        self._period = PeriodSlider("Repeat every")
        # Keep the slider's footprint reserved while hidden so toggling Loop
        # doesn't shift the surrounding content.
        period_policy = self._period.sizePolicy()
        period_policy.setRetainSizeWhenHidden(True)
        self._period.setSizePolicy(period_policy)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.addWidget(self._build_effect_group())
        layout.addStretch(1)

        # Repeat interval only applies when looping — hidden otherwise.
        self._period.setVisible(self._loop.isChecked())

    def _build_effect_group(self) -> QGroupBox:
        box = QGroupBox("Effect")
        box.setObjectName("hapticEffect")
        box.setStyleSheet(group_title_style("hapticEffect", TEAL))
        layout = QVBoxLayout(box)

        top = QHBoxLayout()
        self._loop = QCheckBox("Loop")
        self._loop.toggled.connect(self._on_loop_toggled)
        top.addWidget(self._loop)
        top.addSpacing(8)
        top.addWidget(self._period)
        top.addStretch(1)
        layout.addLayout(top)

        layout.addWidget(QLabel("Effect (fills the waveforms below):"))
        grid = QGridLayout()
        cols = 5
        for idx, (label, pattern) in enumerate(HAPTIC_EFFECTS):
            btn = QPushButton(label)
            btn.setStyleSheet(preset_button_style())
            btn.setToolTip(f"Waveforms: {', '.join(str(w) for w in pattern)}")
            btn.clicked.connect(lambda _checked=False, p=pattern: self._fill_waveforms(p))
            grid.addWidget(btn, idx // cols, idx % cols)
        layout.addLayout(grid)

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

    def _on_loop_toggled(self, checked: bool) -> None:
        # Turning Loop off cancels any running repeat; show the interval only
        # while looping.
        self._sequence_timer.stop()
        self._period.setVisible(checked)

    def _make_waveform_spin(self, default: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 255)
        spin.setValue(default)
        return spin

    def _fill_waveforms(self, pattern: tuple[int, ...]) -> None:
        self._w1_spin.setValue(pattern[0] if len(pattern) > 0 else 0)
        self._w2_spin.setValue(pattern[1] if len(pattern) > 1 else 0)
        self._w3_spin.setValue(pattern[2] if len(pattern) > 2 else 0)

    def _waveforms(self) -> list[int]:
        return [w for w in (self._w1_spin.value(), self._w2_spin.value(), self._w3_spin.value()) if w > 0]

    def _fire_sequence_tick(self) -> None:
        period_ms = self._period.value()
        # Clear must fire before next tick or the dedupe breaker re-engages.
        clear_delay_s = (period_ms / 1000.0) / 2.0
        self._client.hwave_oneshot(*self._sequence_waveforms, clear_delay_s=clear_delay_s)
        if self._restore_led is not None:
            self._restore_led()

    def send(self) -> None:
        # Any Send cancels a running loop — it restarts below if Loop is on.
        self._sequence_timer.stop()
        waveforms = self._waveforms()
        if not waveforms:
            print("[invalid] haptic requires at least one waveform > 0")
            return
        if self._loop.isChecked():
            self._sequence_waveforms = tuple(waveforms)
            self._fire_sequence_tick()
            self._sequence_timer.start(self._period.value())
        else:
            self._client.hwave_oneshot(*waveforms)
            if self._restore_led is not None:
                self._restore_led()

    def emergency_stop(self) -> None:
        """Called by the top-level Stop button. Cancels the local loop timer so
        the next click of Send starts fresh."""
        self._sequence_timer.stop()
