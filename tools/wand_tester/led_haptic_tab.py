"""Combined LED + periodic haptic tab — firmware-clean single-CMD1 combos."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QVBoxLayout,
    QWidget,
)

from wand.streaming.eliko.pekio_client import PekioClient

from wand_tester.widgets import (
    ColourPicker,
    PeriodSlider,
    build_blink_group,
    build_solid_group,
)


class LedHapticTab(QWidget):
    """Combined LED + periodic haptic — single CMD1 sets both, firmware
    manages the periodicity (no Python timer, no LED flicker).

    Firmware constraints intentionally narrow the option set here:
      - Solid LED + periodic buzz: clean.
      - Blink LED (presets + custom) + periodic buzz: clean.
      - Fade LED + buzz: firmware ignores the haptic bit in fade mode — use
        the LED tab for fade; haptic can't ride alongside in one CMD1.
      - Hwave/Sequence + LED: hwave's CMD1 form has no LED bits. Use the
        Haptic tab — it re-fires the last LED command after each hwave
        which is the only way to combine the two on this firmware.
    """

    def __init__(self, client: PekioClient) -> None:
        super().__init__()
        self._client = client
        self._command_group = QButtonGroup(self)
        self._command_group.setExclusive(True)
        self._selected_method: str = "solid"

        self._colour_picker = ColourPicker()
        blink = build_blink_group(self._command_group, self._set_method)
        self._blink_period_spin = blink.period_spin
        self._blink_duty_spin = blink.duty_spin
        self._period = PeriodSlider("Haptic Period")

        layout = QVBoxLayout(self)
        layout.addWidget(self._colour_picker)
        layout.addWidget(build_solid_group(self._command_group, self._set_method))
        layout.addWidget(blink.box)
        layout.addWidget(self._period)
        layout.addStretch(1)

    def _set_method(self, method: str) -> None:
        self._selected_method = method

    def send(self) -> None:
        method = self._selected_method
        colour = self._colour_picker.selected
        buzz_ms = self._period.value()
        if method == "blink_custom":
            period = self._blink_period_spin.value()
            duty = self._blink_duty_spin.value()
            if duty >= period:
                print(f"[invalid] blink duty ({duty}) must be < period ({period})")
                return
            self._client.blink(period, duty, colour, buzz=buzz_ms)
        else:
            getattr(self._client, method)(colour, buzz=buzz_ms)

    def emergency_stop(self) -> None:
        """No widget-local timers — combined CMD1 is firmware-managed, and
        Stop All routes through client.stop_all()."""
