from __future__ import annotations

import random
import time
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_tag import SpellTag
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

    `AutoAdvanceSettings.enabled_tags` restricts the Up/Down cycle, the auto-advance
    pool, and the dropdown options to zones whose spells carry an enabled tag;
    explicit numeric-key selection still reaches any zone.
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
        spell_tags: dict[SpellType, frozenset[SpellTag]],
        cast_recognized: Event[Callable[[SpellCastQuality], None]],
        set_zone_options: Callable[[list[tuple[str | None, str]], str | None], None],
        enabled_tags_changed: Event[Callable[[frozenset[SpellTag]], None]],
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
        # A zone's tags are the union of its spells' tags; it is eligible when that
        # union intersects the enabled set.
        self._zone_tags: dict[str, frozenset[SpellTag]] = {
            zone.id: frozenset().union(*(spell_tags.get(spell, frozenset()) for spell in zone.spells))
            if zone.spells
            else frozenset()
            for zone in zones
        }
        self._current: str | None = None
        # Shuffle bag for randomised auto-advance: draw without replacement until
        # empty, then reshuffle, so every spell appears once per pass.
        self._shuffle_bag: list[str] = []

        self._numeric_buffer = ""
        self._numeric_last_press = 0.0

        self._key_pressed.subscribe(self._on_key)
        self._zone_selected.subscribe(self._on_zone_selected)
        cast_recognized.subscribe(self._on_cast_recognized)
        enabled_tags_changed.subscribe(self._on_enabled_tags_changed)

        self._push_zone_options()

    def select_default_zone(self) -> None:
        """Select the start-up zone: a shuffle-bag draw when randomising, else the first eligible."""
        if self._settings.auto_advance and self._settings.randomise:
            pool = [zone_id for zone_id in self._cycle_values() if zone_id is not None]
            if pool:
                self._apply(self._draw_from_shuffle_bag(pool))
                return
        self._apply(self._first_eligible_zone())

    def _first_eligible_zone(self) -> str | None:
        """First zone the cycle would land on (tag-filtered), or None."""
        eligible = [zone_id for zone_id in self._cycle_values() if zone_id is not None]
        return eligible[0] if eligible else None

    def _is_eligible(self, zone_id: str) -> bool:
        return bool(self._zone_tags[zone_id] & self._settings.enabled_tags)

    def _on_enabled_tags_changed(self, _: frozenset[SpellTag]) -> None:
        # Refilter the dropdown; if the current zone just fell out of the pool, move to
        # the first eligible one so we never sit on a hidden zone.
        if self._current is not None and not self._is_eligible(self._current):
            self._apply(self._first_eligible_zone())  # _apply repushes options
        else:
            self._push_zone_options()

    def _push_zone_options(self) -> None:
        """Publish the dropdown option list, filtered to zones with an enabled tag."""
        options: list[tuple[str | None, str]] = [(None, "(none)")]
        for zone in self._zones:
            if not self._is_eligible(zone.id):
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
        """Move to the next spell/zone: shuffle-bag draw, or sequential from the current."""
        pool = [zone_id for zone_id in self._cycle_values() if zone_id is not None]
        if not pool:
            self._logger.debug("Auto-advance: no eligible zones (tag filter empty?)")
            return

        if self._settings.randomise:
            zone_id = self._draw_from_shuffle_bag(pool)
        else:
            try:
                idx = pool.index(self._current)
                zone_id = pool[(idx + 1) % len(pool)]
            except ValueError:
                zone_id = pool[0]

        self._apply(zone_id)

    def _draw_from_shuffle_bag(self, pool: list[str]) -> str:
        """Draw the next zone without replacement; refill and reshuffle when the bag empties."""
        # Drop entries no longer eligible (the tag filter can change between casts).
        self._shuffle_bag = [zone_id for zone_id in self._shuffle_bag if zone_id in pool]
        if not self._shuffle_bag:
            self._shuffle_bag = random.sample(pool, len(pool))
            # Avoid a back-to-back repeat across the bag boundary.
            if len(self._shuffle_bag) > 1 and self._shuffle_bag[0] == self._current:
                self._shuffle_bag.append(self._shuffle_bag.pop(0))
        return self._shuffle_bag.pop(0)

    def _cycle_values(self) -> list[str | None]:
        """Cycle universe: `(none)` plus the zones whose tags intersect the enabled set."""
        return [None, *[zone_id for zone_id in self._zone_ids if self._is_eligible(zone_id)]]

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
