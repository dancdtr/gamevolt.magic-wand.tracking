from __future__ import annotations

from gamevolt.logging._logger import Logger
from services.models.spell_cast_result import SpellCastResult
from services.spell_cast_reporter_base import SpellCastReporterBase
from services.wizard_session_store import WizardSessionStore
from show_system.show_system_controller import ShowSystemController
from spells.spell_match import SpellMatch
from spells.spell_type import SpellType
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
        wizard_level = self._get_wizard_level(match.wand_id)
        spell_level = SPELL_REQUIREMENTS.get(match.spell_type, WizardLevel.BEGINNER)
        success = self._has_sufficient_level(wizard_level, spell_level)

        self._show_system_controller.play_spell(match.spell_type, wizard_level)

        cast_message = "successfully cast" if success else "under cast"
        self._logger.debug(
            f"'{wizard_level.name}' wizard with wand ({match.wand_id}) {cast_message} "
            f"'{spell_level.name}' spell '{match.spell_type.name}'."
        )

        return SpellCastResult(wand_id=match.wand_id, spell_name=match.spell_name, success=success)

    def _get_wizard_level(self, wand_id: str) -> WizardLevel:
        profile = self._session_store.get(wand_id)
        if profile is None:
            self._logger.warning(f"No profile in session store for wand ({wand_id}); defaulting to BEGINNER")
            return WizardLevel.BEGINNER
        return profile.wizard_level

    @staticmethod
    def _has_sufficient_level(wizard_level: WizardLevel, spell_level: WizardLevel) -> bool:
        if wizard_level == WizardLevel.BEGINNER and spell_level != WizardLevel.BEGINNER:
            return False
        if wizard_level == WizardLevel.INTERMEDIATE and spell_level == WizardLevel.ADVANCED:
            return False
        return True
