from __future__ import annotations

import time
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from zones.mock_zone_manager import MockZoneManager

_NUMERIC_INPUT_WINDOW_S = 0.5


class QtZoneControls:
    """Keyboard zone selection inside the Qt window (replaces the tkinter MockZoneControls).

    Inputs (all route through `MockZoneManager.set_current_zone`):
      - the window's `key_pressed` token stream: digit keys (0-9) build a multi-digit
        number within a 0.5s window addressing `ZoneSettings.key`; Up / Down cycle
        prev/next through `(none)` + configured zones, wrapping;
      - the window's `zone_selected` dropdown picks.
    """

    def __init__(
        self,
        logger: Logger,
        zone_manager: MockZoneManager,
        zone_ids: list[str],
        key_map: dict[int, str],
        key_pressed: Event[Callable[[str], None]],
        zone_selected: Event[Callable[[str | None], None]],
    ) -> None:
        self._logger = logger
        self._zone_manager = zone_manager
        self._key_map = dict(key_map)
        self._key_pressed = key_pressed
        self._zone_selected = zone_selected

        self._values: list[str | None] = [None, *zone_ids]
        self._current_idx = 0

        self._numeric_buffer = ""
        self._numeric_last_press = 0.0

        self._key_pressed.subscribe(self._on_key)
        self._zone_selected.subscribe(self._on_zone_selected)

    def dispose(self) -> None:
        self._key_pressed.unsubscribe(self._on_key)
        self._zone_selected.unsubscribe(self._on_zone_selected)

    def _on_zone_selected(self, zone_id: str | None) -> None:
        if zone_id in self._values:
            self._current_idx = self._values.index(zone_id)
        self._apply(zone_id)

    def _on_key(self, token: str) -> None:
        if token in ("Up", "Down"):
            self._cycle(-1 if token == "Up" else 1)
        elif token.isdigit():
            self._on_digit(token)

    def _cycle(self, step: int) -> None:
        self._current_idx = (self._current_idx + step) % len(self._values)
        self._apply(self._values[self._current_idx])

    def _on_digit(self, digit: str) -> None:
        now = time.monotonic()
        if not self._numeric_buffer or (now - self._numeric_last_press) > _NUMERIC_INPUT_WINDOW_S:
            self._numeric_buffer = digit
        else:
            self._numeric_buffer += digit
        self._numeric_last_press = now

        key = int(self._numeric_buffer)
        zone_id = self._key_map.get(key)
        if zone_id is None:
            self._logger.debug(f"Numeric input '{self._numeric_buffer}': no zone bound to key {key}")
            return

        if zone_id in self._values:
            self._current_idx = self._values.index(zone_id)
        self._apply(zone_id)

    def _apply(self, zone_id: str | None) -> None:
        self._logger.debug(f"Mock zone selection: {zone_id}")
        self._zone_manager.set_current_zone(zone_id)
