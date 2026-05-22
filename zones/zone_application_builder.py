from __future__ import annotations

from display.image_libraries.spell_image_library import SpellImageLibrary
from gamevolt.logging import Logger
from gamevolt.visualisation.visualiser import Visualiser
from spells.spell_registry import SpellRegistry
from visualisation.spell_target_visualiser import SpellTargetVisualiser
from zones.mock_zone_controls import MockZoneControls
from zones.mock_zone_manager import MockZoneManager
from zones.visualisation.null_zone_visualiser import NullZoneVisualiser
from zones.visualisation.zone_presentation_controller import ZonePresentationController
from zones.zone_application import ZoneApplication

WANDS_IDS = ["E000"]


class ZoneApplicationBuilder:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def build_mock(self, spell_registry: SpellRegistry, visualiser: Visualiser, spell_image_library: SpellImageLibrary) -> ZoneApplication:
        zone_manager = MockZoneManager(
            logger=self._logger,
            spell_registry=spell_registry,
            wand_ids=WANDS_IDS,
        )

        zone_visualiser = SpellTargetVisualiser(
            logger=self._logger,
            spell_image_library=spell_image_library,
            visualiser=visualiser,
        )

        controls = MockZoneControls(
            logger=self._logger,
            spell_registry=spell_registry,
            zone_manager=zone_manager,
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

    def build_production(self, zone_manager) -> ZoneApplication:
        zone_visualiser = NullZoneVisualiser()

        presentation = ZonePresentationController(
            logger=self._logger,
            zone_manager=zone_manager,
            visualiser=zone_visualiser,
        )

        return ZoneApplication(
            logger=self._logger,
            zone_manager=zone_manager,
            presentation_controller=presentation,
            controls=None,
        )
