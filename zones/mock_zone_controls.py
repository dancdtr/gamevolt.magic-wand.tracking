from __future__ import annotations

import time
import tkinter as tk
import tkinter.ttk as ttk

from gamevolt.logging import Logger
from zones.mock_zone_manager import MockZoneManager


class MockZoneControls:
    """Tk dropdown + keyboard shortcuts for picking the current mock zone.

    Inputs (all route through `MockZoneManager.set_current_zone`, which swaps
    every tracked wand in one shot):

    - Dropdown selection — explicit click pick from configured zone ids + `(none)`.
    - Up / Down — cycle prev/next, wrapping (includes the `(none)` slot).
    - Digit keys (0-9) — type one or more digits to address `ZoneSettings.key`.
      Successive presses inside `_NUMERIC_INPUT_WINDOW_S` build a multi-digit
      number (e.g. `2` then `3` → 23); past the window, the buffer resets.
      Each press attempts a lookup; numbers with no matching zone are logged
      and ignored, but the buffer keeps building so a longer sequence can
      still match.
    """

    _NONE_LABEL = "(none)"
    _NUMERIC_INPUT_WINDOW_S = 0.5

    def __init__(
        self,
        logger: Logger,
        zone_manager: MockZoneManager,
        zone_ids: list[str],
        key_map: dict[int, str],
        root: tk.Misc,
        parent: tk.Misc | None = None,
    ) -> None:
        self._logger = logger
        self._zone_manager = zone_manager
        self._zone_ids = list(zone_ids)
        self._key_map = dict(key_map)

        host = parent or root
        frame = tk.Frame(host)
        frame.pack(fill="x", padx=8, pady=6)

        tk.Label(frame, text="Zone:").pack(side="left", padx=(0, 6))

        self._values = [self._NONE_LABEL, *self._zone_ids]
        self._choice = tk.StringVar(value=self._NONE_LABEL)
        self._combo = ttk.Combobox(frame, textvariable=self._choice, values=self._values, state="readonly")
        self._combo.pack(side="left", fill="x", expand=True)
        self._combo.bind("<<ComboboxSelected>>", self._on_selected)

        # Up / Down cycle through (none) + configured zones, wrapping.
        root.bind_all("<Up>", lambda _e: self._cycle(-1))
        root.bind_all("<Down>", lambda _e: self._cycle(1))

        # Digit keys feed the numeric-input buffer.
        for digit in range(10):
            root.bind_all(f"<Key-{digit}>", lambda _e, d=str(digit): self._on_digit(d))

        self._numeric_buffer: str = ""
        self._numeric_last_press: float = 0.0

    def _on_selected(self, _event: tk.Event) -> None:
        self._apply(self._choice.get())

    def _cycle(self, step: int) -> None:
        try:
            current_idx = self._values.index(self._choice.get())
        except ValueError:
            current_idx = 0
        next_idx = (current_idx + step) % len(self._values)
        selection = self._values[next_idx]
        self._choice.set(selection)
        self._apply(selection)

    def _on_digit(self, digit: str) -> None:
        now = time.monotonic()
        if not self._numeric_buffer or (now - self._numeric_last_press) > self._NUMERIC_INPUT_WINDOW_S:
            self._numeric_buffer = digit
        else:
            self._numeric_buffer += digit
        self._numeric_last_press = now

        key = int(self._numeric_buffer)
        zone_id = self._key_map.get(key)
        if zone_id is None:
            self._logger.debug(f"Numeric input '{self._numeric_buffer}': no zone bound to key {key}")
            return

        self._choice.set(zone_id)
        self._apply(zone_id)

    def _apply(self, selection: str) -> None:
        zone_id = None if selection == self._NONE_LABEL else selection
        self._logger.debug(f"Mock zone selection: {zone_id}")
        self._zone_manager.set_current_zone(zone_id)
