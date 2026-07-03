from __future__ import annotations

import random
import time
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from spells.spell_cast_quality import SpellCastQuality
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
      - `cast_recognized`: on a recognized cast, auto-advance to the next spell when
        `AutoAdvanceSettings.auto_advance` is on and the cast met
        `AutoAdvanceSettings.min_advance_quality`.

    `in_park_only` restricts the Up/Down cycle, the auto-advance pool, and the dropdown
    options to in-park spells; explicit numeric-key selection still reaches any zone.
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
        cast_recognized: Event[Callable[[SpellCastQuality], None]],
        set_zone_options: Callable[[list[tuple[str | None, str]], str | None], None],
        in_park_only_changed: Event[Callable[[bool], None]],
    ) -> None:
        self._logger = logger
        self._zone_manager = zone_manager
        self._zones = list(zones)
        self._key_map = dict(key_map)
        self._key_pressed = key_pressed
        self._zone_selected = zone_selected
        self._settings = settings
        self._set_zone_options = set_zone_options

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
        in_park_only_changed.subscribe(self._on_in_park_only_changed)

        self._push_zone_options()

    def select_default_zone(self) -> None:
        """Select the start-up zone: the first eligible zone under the current filter."""
        self._apply(self._first_eligible_zone())

    def _first_eligible_zone(self) -> str | None:
        """First zone the cycle would land on (in-park when the filter is on), or None."""
        eligible = [zone_id for zone_id in self._cycle_values() if zone_id is not None]
        return eligible[0] if eligible else None

    def _on_in_park_only_changed(self, in_park_only: bool) -> None:
        # Refilter the dropdown; if the current zone just fell out of the pool, move to
        # the first eligible one so we never sit on a hidden zone.
        if in_park_only and self._current is not None and not self._in_park[self._current]:
            self._apply(self._first_eligible_zone())  # _apply repushes options
        else:
            self._push_zone_options()

    def _push_zone_options(self) -> None:
        """Publish the dropdown option list, filtered to in-park zones when enabled."""
        options: list[tuple[str | None, str]] = [(None, "(none)")]
        for zone in self._zones:
            if self._settings.in_park_only and not self._in_park[zone.id]:
                continue
            spells = ", ".join(spell.name for spell in zone.spells)
            options.append((zone.id, f"{zone.id} - {spells}" if spells else zone.id))
        self._set_zone_options(options, self._current)

    def _on_zone_selected(self, zone_id: str | None) -> None:
        self._apply(zone_id)

    def _on_key(self, token: str) -> None:
        if token in ("Up", "Down"):
            self._cycle(-1 if token == "Up" else 1)
        elif token.isdigit():
            self._on_digit(token)

    def _on_cast_recognized(self, quality: SpellCastQuality) -> None:
        if not self._settings.auto_advance:
            return
        # Only advance when the cast met the configured minimum tier; a weaker cast
        # stays on the same spell so the player can retry and improve.
        if quality.value < self._settings.min_advance_quality.value:
            self._logger.debug(
                f"Cast quality {quality.name} below advance minimum "
                f"{self._settings.min_advance_quality.name}; staying on spell."
            )
            return
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
        # Refresh the dropdown (filter + selection) before driving presence so the combo's
        # index map is current when `show_zone` re-selects the active zone.
        self._push_zone_options()
        self._zone_manager.set_current_zone(zone_id)
