from __future__ import annotations

from typing import cast

from gamevolt.logging import Logger
from spells.spell_selection import load_included_spells
from visualisation.qt.qt_zone_controls import QtZoneControls
from visualisation.visualiser_protocol import WandVisualiserProtocol
from zones.configuration.zones_settings import ZonesSettings
from zones.mock_zone_manager import MockZoneManager
from zones.visualisation.zone_presentation_controller import ZonePresentationController
from zones.visualisation.zone_visualiser_protocol import ZoneVisualiserProtocol
from zones.zone_application import ZoneApplication
from zones.zone_factory import ZoneFactory
from zones.zone_manager_protocol import ZoneManagerProtocol


class ZoneApplicationBuilder:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def build_mock(
        self,
        zones_settings: ZonesSettings,
        zone_factory: ZoneFactory,
        visualiser: WandVisualiserProtocol,
        wand_ids: list[str],
    ) -> ZoneApplication:
        zone_manager = MockZoneManager(
            logger=self._logger,
            settings=zones_settings,
            zone_factory=zone_factory,
            wand_ids=wand_ids,
        )

        # The unified Qt window doubles as the zone visualiser + key source. When the
        # visualiser is headless it lacks these, so the mock simply runs without UI.
        if not (hasattr(visualiser, "show_zone") and hasattr(visualiser, "key_pressed")):
            return ZoneApplication(logger=self._logger, zone_manager=zone_manager)

        presentation = ZonePresentationController(
            logger=self._logger,
            zone_manager=zone_manager,
            visualiser=cast(ZoneVisualiserProtocol, visualiser),
        )

        controls = QtZoneControls(
            logger=self._logger,
            zone_manager=zone_manager,
            zones=list(zones_settings.zones),
            key_map=self._build_zone_key_map(zones_settings),
            key_pressed=visualiser.key_pressed,  # type: ignore[attr-defined]
            zone_selected=visualiser.zone_selected,  # type: ignore[attr-defined]
            settings=visualiser.auto_advance_settings,  # type: ignore[attr-defined]
            included_spells=load_included_spells(self._logger),
            cast_recognized=visualiser.cast_recognized,  # type: ignore[attr-defined]
            set_zone_options=visualiser.set_zone_options,  # type: ignore[attr-defined]
            in_park_only_changed=visualiser.in_park_only_changed,  # type: ignore[attr-defined]
        )

        return ZoneApplication(
            logger=self._logger,
            zone_manager=zone_manager,
            presentation_controller=presentation,
            controls=controls,
            # Start in the first eligible zone (first in-park spell when the filter is on)
            # rather than '(none)'. Deferred to start-up so subscribers are wired first.
            on_started=controls.select_default_zone,
        )

    def build_production(self, zone_manager: ZoneManagerProtocol) -> ZoneApplication:
        # Production has no spell-target visualiser and no UI controls: zone
        # presence comes from real positioning; downstream consumers react to
        # the manager's events directly.
        return ZoneApplication(
            logger=self._logger,
            zone_manager=zone_manager,
            presentation_controller=None,
            controls=None,
        )

    @staticmethod
    def _build_zone_key_map(zones_settings: ZonesSettings) -> dict[int, str]:
        """Map int shortcut key → zone id. Raises if two zones claim the same key."""
        key_map: dict[int, str] = {}
        for zone in zones_settings.zones:
            existing = key_map.get(zone.key)
            if existing is not None:
                raise ValueError(
                    f"Zone shortcut key {zone.key} is bound to both '{existing}' and '{zone.id}'."
                )
            key_map[zone.key] = zone.id
        return key_map
