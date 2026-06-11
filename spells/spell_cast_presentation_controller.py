from __future__ import annotations

import asyncio
from logging import Logger

from spells.spell_cast import SpellCast
from visualisation.wand_colour_registry import WandColourRegistry
from wand.tracked_wand_manager import TrackedWandManager
from zones.visualisation.zone_visualiser_protocol import ZoneVisualiserProtocol

COLOUR_FLASH_DURATION = 0.3
FALLBACK_COLOUR = "#999999"


class SpellCastPresentationController:
    def __init__(
        self,
        logger: Logger,
        tracked_wand_manager: TrackedWandManager,
        zone_visualiser: ZoneVisualiserProtocol,
        colour_assigner: WandColourRegistry,
    ):
        self._logger = logger
        self._tracked_wand_manager = tracked_wand_manager
        self._zone_visualiser = zone_visualiser
        self._colour_assigner = colour_assigner

    async def start_async(self) -> None:
        self._tracked_wand_manager.spell_cast.subscribe(self._on_spell_cast)

    async def stop_async(self) -> None:
        self._tracked_wand_manager.spell_cast.unsubscribe(self._on_spell_cast)

    def _on_spell_cast(self, cast: SpellCast) -> None:
        colour = self._colour_assigner.try_get_known(cast.wand_id) or FALLBACK_COLOUR

        self._zone_visualiser.show_spell_cast_coloured(cast.spell_type, colour)

        async def _restore() -> None:
            await asyncio.sleep(COLOUR_FLASH_DURATION)
            self._zone_visualiser.show_spell_instruction(cast.spell_type)

        asyncio.create_task(_restore())
