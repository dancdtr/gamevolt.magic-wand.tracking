from __future__ import annotations

import asyncio
from logging import Logger

from services.spell_cast_reporter_base import SpellCastReporterBase
from spells.spell_match import SpellMatch
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_device_controller import WandDeviceController


class WandSpellCueController:
    def __init__(
        self,
        logger: Logger,
        tracked_wand_manager: TrackedWandManager,
        wand_device_controller: WandDeviceController,
        spell_cast_reporter: SpellCastReporterBase,
    ) -> None:
        self._wand_device_controller = wand_device_controller
        self._tracked_wand_manager = tracked_wand_manager
        self._spell_cast_reporter = spell_cast_reporter
        self._logger = logger

    def start(self) -> None:
        self._tracked_wand_manager.spell_cast.subscribe(self._on_spell_cast)

    def stop(self) -> None:
        self._tracked_wand_manager.spell_cast.unsubscribe(self._on_spell_cast)

    def _on_spell_cast(self, match: SpellMatch) -> None:
        asyncio.create_task(self._handle_cast(match))

    async def _handle_cast(self, match: SpellMatch) -> None:
        try:
            result = await self._spell_cast_reporter.report_spell_cast(match)
        except Exception:
            self._logger.exception(f"Spell cast report failed for wand ({match.wand_id})")
            return

        self._wand_device_controller.play_spell_cast_cue(match.wand_id, result.success)
