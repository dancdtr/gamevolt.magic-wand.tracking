from __future__ import annotations

from gamevolt.logging._logger import Logger
from services.models.spell_cast_result import SpellCastResult
from services.spell_cast_reporter_base import SpellCastReporterBase
from services.wizard_session_store import WizardSessionStore
from show_system.show_system_controller import ShowSystemController
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_match import SpellMatch
from spells.spell_type import SpellType
from wizards.hogwarts_house import HogwartsHouse
from wizards.wizard_level import WizardLevel

SPELL_REQUIREMENTS: dict[SpellType, WizardLevel] = {
    SpellType.RICTUSEMPRA: WizardLevel.BEGINNER,
    SpellType.REPARO: WizardLevel.BEGINNER,
    SpellType.PEPPER_BREATH: WizardLevel.INTERMEDIATE,
    SpellType.APARECIUM: WizardLevel.INTERMEDIATE,
    SpellType.CANTIS: WizardLevel.ADVANCED,
}


class LocalSpellCastReporter(SpellCastReporterBase):
    """Stand-in for the hub's spell-cast endpoint. Determines success locally and triggers the show."""

    def __init__(
        self,
        logger: Logger,
        session_store: WizardSessionStore,
        show_system_controller: ShowSystemController,
    ) -> None:
        self._logger = logger
        self._session_store = session_store
        self._show_system_controller = show_system_controller

    async def report_spell_cast(self, match: SpellMatch) -> SpellCastResult:
        house = self._get_hogwarts_house(match.wand_id)
        bonus = self._get_wizard_bonus(match.wand_id)
        quality = self._get_spell_cast_quality(match, bonus)

        self._show_system_controller.play_spell(match.spell_type, quality, house)

        self._logger.debug(f"Wizard with wand ({match.wand_id}) cast spell '{match.spell_type.name}' with quality: {quality}.")

        return SpellCastResult(wand_id=match.wand_id, spell_name=match.spell_name, quality=quality)

    def _get_wizard_bonus(self, wand_id: str) -> int:
        profile = self._session_store.get(wand_id)
        if profile is None:
            self._logger.warning(f"No profile in session store for wand ({wand_id}); defaulting to BEGINNER")
            return 0
        return profile.spell_cast_bonus

    def _get_spell_cast_quality(self, match: SpellMatch, bonus: int) -> SpellCastQuality:
        return SpellCastQuality.SKILLED

    def _get_hogwarts_house(self, wand_id: str) -> HogwartsHouse:
        return HogwartsHouse.GRYFFINDOR

    @staticmethod
    def _has_sufficient_level(wizard_level: WizardLevel, spell_level: WizardLevel) -> bool:
        if wizard_level == WizardLevel.BEGINNER and spell_level != WizardLevel.BEGINNER:
            return False
        if wizard_level == WizardLevel.INTERMEDIATE and spell_level == WizardLevel.ADVANCED:
            return False
        return True
