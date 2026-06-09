from __future__ import annotations

from display.image_libraries.spell_image_library import SpellImageLibrary
from gamevolt.logging import Logger
from gamevolt.visualisation.visualiser import Visualiser
from visualisation.spell_target_visualiser import SpellTargetVisualiser
from zones.configuration.zones_settings import ZonesSettings
from zones.mock_zone_controls import MockZoneControls
from zones.mock_zone_manager import MockZoneManager
from zones.visualisation.zone_presentation_controller import ZonePresentationController
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
        visualiser: Visualiser,
        spell_image_library: SpellImageLibrary,
        wand_ids: list[str],
    ) -> ZoneApplication:
        zone_manager = MockZoneManager(
            logger=self._logger,
            settings=zones_settings,
            zone_factory=zone_factory,
            wand_ids=wand_ids,
        )

        zone_visualiser = SpellTargetVisualiser(
            logger=self._logger,
            spell_image_library=spell_image_library,
            visualiser=visualiser,
        )

        key_map = self._build_zone_key_map(zones_settings)
        controls = MockZoneControls(
            logger=self._logger,
            zone_manager=zone_manager,
            zone_ids=[zone.id for zone in zones_settings.zones],
            key_map=key_map,
            root=visualiser.root,
        )

        presentation = ZonePresentationController(
            logger=self._logger,
            zone_manager=zone_manager,
            visualiser=zone_visualiser,
        )

        return ZoneApplication(
            logger=self._logger,
            zone_manager=zone_manager,
            presentation_controller=presentation,
            controls=controls,
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
