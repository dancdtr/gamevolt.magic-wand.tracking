from __future__ import annotations

from gamevolt.logging._logger import Logger
from services.models.spell_cast_result import SpellCastResult
from services.spell_cast_reporter_base import SpellCastReporterBase
from services.wizard_session_store import WizardSessionStore
from show_system.show_system_controller import ShowSystemController
from spells.spell_cast import SpellCast
from wizards.hogwarts_house import HogwartsHouse


class LocalSpellCastReporter(SpellCastReporterBase):
    """Stand-in for the hub's spell-cast endpoint. Triggers the show for a recognised cast.

    The quality tier is now decided upstream by the SpellScorer and carried on the SpellCast;
    this reporter no longer grades — it just plays the show and records the result.
    """

    def __init__(
        self,
        logger: Logger,
        session_store: WizardSessionStore,
        show_system_controller: ShowSystemController,
    ) -> None:
        self._logger = logger
        self._session_store = session_store
        self._show_system_controller = show_system_controller

    async def report_spell_cast(self, cast: SpellCast) -> SpellCastResult:
        house = self._get_hogwarts_house(cast.wand_id)
        quality = cast.quality

        self._show_system_controller.play_spell(cast.wand_id, cast.spell_type, quality, house)

        self._logger.debug(f"Wizard with wand ({cast.wand_id}) cast spell '{cast.spell_name}' with quality: {quality.name}.")

        return SpellCastResult(wand_id=cast.wand_id, spell_name=cast.spell_name, quality=quality)

    def _get_hogwarts_house(self, wand_id: str) -> HogwartsHouse:
        return HogwartsHouse.GRYFFINDOR
