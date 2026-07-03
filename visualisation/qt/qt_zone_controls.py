from __future__ import annotations

import random
import time
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from spells.spell_type import SpellType
from visualisation.qt.auto_advance_settings import AutoAdvanceSettings
from zones.configuration.zone_settings import ZoneSettings
from zones.mock_zone_manager import MockZoneManager

_NUMERIC_INPUT_WINDOW_S = 0.5


class QtZoneControls:
    """Keyboard zone selection inside the Qt window (replaces the tkinter MockZoneControls).

    Inputs (all route through `MockZoneManager.set_current_zone`):
      - the window's `key_pressed` token stream: digit keys (0-9) build a multi-digit
        number within a 0.5s window addressing `ZoneSettings.key`; Up / Down cycle
        prev/next through `(none)` + zones, wrapping;
      - the window's `zone_selected` dropdown picks;
      - `cast_recognized`: on a rudimentary+ cast, auto-advance to the next spell when
        `AutoAdvanceSettings.auto_advance` is on.

    `in_park_only` restricts the Up/Down cycle and the auto-advance pool to in-park
    spells; explicit numeric-key / dropdown selection still reaches any zone.
    """

    def __init__(
        self,
        logger: Logger,
        zone_manager: MockZoneManager,
        zones: list[ZoneSettings],
        key_map: dict[int, str],
        key_pressed: Event[Callable[[str], None]],
        zone_selected: Event[Callable[[str | None], None]],
        settings: AutoAdvanceSettings,
        included_spells: frozenset[SpellType],
        cast_recognized: Event[Callable[[], None]],
    ) -> None:
        self._logger = logger
        self._zone_manager = zone_manager
        self._key_map = dict(key_map)
        self._key_pressed = key_pressed
        self._zone_selected = zone_selected
        self._settings = settings

        self._zone_ids = [zone.id for zone in zones]
        # A zone counts as in-park if any of its spells ships in the theme-park selection.
        self._in_park = {
            zone.id: any(spell in included_spells for spell in zone.spells) for zone in zones
        }
        self._current: str | None = None

        self._numeric_buffer = ""
        self._numeric_last_press = 0.0

        self._key_pressed.subscribe(self._on_key)
        self._zone_selected.subscribe(self._on_zone_selected)
        cast_recognized.subscribe(self._on_cast_recognized)

    def select_zone_by_key(self, key: int) -> None:
        """Select the zone bound to a shortcut key (e.g. start-up default)."""
        zone_id = self._key_map.get(key)
        if zone_id is None:
            self._logger.debug(f"No zone bound to key {key}; nothing selected.")
            return
        self._apply(zone_id)

    def _on_zone_selected(self, zone_id: str | None) -> None:
        self._apply(zone_id)

    def _on_key(self, token: str) -> None:
        if token in ("Up", "Down"):
            self._cycle(-1 if token == "Up" else 1)
        elif token.isdigit():
            self._on_digit(token)

    def _on_cast_recognized(self) -> None:
        if self._settings.auto_advance:
            self._advance()

    def _cycle(self, step: int) -> None:
        values = self._cycle_values()  # [None, *zones], park-filtered when enabled
        try:
            idx = values.index(self._current)
        except ValueError:
            idx = 0
        self._apply(values[(idx + step) % len(values)])

    def _advance(self) -> None:
        """Move to the next spell/zone: random pick, or sequential from the current."""
        pool = [zone_id for zone_id in self._cycle_values() if zone_id is not None]
        if not pool:
            self._logger.debug("Auto-advance: no eligible zones (in-park filter empty?)")
            return

        if self._settings.randomise:
            others = [zone_id for zone_id in pool if zone_id != self._current]
            zone_id = random.choice(others or pool)
        else:
            try:
                idx = pool.index(self._current)
                zone_id = pool[(idx + 1) % len(pool)]
            except ValueError:
                zone_id = pool[0]

        self._apply(zone_id)

    def _cycle_values(self) -> list[str | None]:
        """Cycle universe: `(none)` plus zones, filtered to in-park when the toggle is on."""
        if self._settings.in_park_only:
            return [None, *[zone_id for zone_id in self._zone_ids if self._in_park[zone_id]]]
        return [None, *self._zone_ids]

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
        self._apply(zone_id)

    def _apply(self, zone_id: str | None) -> None:
        self._current = zone_id
        self._logger.debug(f"Mock zone selection: {zone_id}")
        self._zone_manager.set_current_zone(zone_id)
