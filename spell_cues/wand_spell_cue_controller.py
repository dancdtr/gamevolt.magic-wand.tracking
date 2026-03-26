from __future__ import annotations

from logging import Logger

from show_system.show_system_controller import ShowSystemController
from spell_cues.configuration.wand_spell_cue_controller_settings import WandSpellCueControllerSettings
from spells.spell_type import SpellType
from wand.tracked_wand import TrackedWand
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_device_controller import WandDeviceController
from wizards.wizard_level_type import WizardLevelType
from wizards.wizard_stats_manager import WizardStatsManager
from zones.zone import Zone

SPELL_REQUIREMENTS: dict[SpellType, WizardLevelType] = {
    SpellType.RICTUSEMPRA: WizardLevelType.BEGINNER,
    SpellType.REPARO: WizardLevelType.BEGINNER,
    SpellType.PEPPER_BREATH: WizardLevelType.INTERMEDIATE,
    SpellType.APARECIUM: WizardLevelType.INTERMEDIATE,
    SpellType.CANTIS: WizardLevelType.ADVANCED,
}


class WandSpellCueController:
    def __init__(
        self,
        logger: Logger,
        settings: WandSpellCueControllerSettings,
        tracked_wand_manager: TrackedWandManager,
        wand_device_controller: WandDeviceController,
        show_system_controller: ShowSystemController,
        wizard_stats_manager: WizardStatsManager,
    ) -> None:
        self._show_system_controller = show_system_controller
        self._wand_device_controller = wand_device_controller
        self._tracked_wand_manager = tracked_wand_manager
        self._wizard_stats_manager = wizard_stats_manager
        self._settings = settings
        self._logger = logger

    def start(self) -> None:
        self._tracked_wand_manager.spell_cast.subscribe(self._on_spell_cast)

    def stop(self) -> None:
        self._tracked_wand_manager.spell_cast.unsubscribe(self._on_spell_cast)

    def _on_spell_cast(self, wand: TrackedWand, zone: Zone, spell_type: SpellType) -> None:
        wizard_level = self._wizard_stats_manager.get_wizard_level(wand.id)
        self._wizard_stats_manager.on_spell_cast(wand.id)
        # wizard_level = self._get_wizard_level(wand.id)

        self._show_system_controller.play_spell(spell_type, wizard_level)
        spell_level = SPELL_REQUIREMENTS.get(spell_type, WizardLevelType.BEGINNER)

        has_sufficient_level = self._has_sufficient_level(wizard_level, spell_level)
        cast_message = f"{'successfully cast' if has_sufficient_level else 'under cast'}"
        self._logger.debug(
            f"'{wizard_level.name.upper()}' wizard with wand ({wand.id}) {cast_message} '{spell_level.name}' spell '{spell_type.name}'."
        )
        self._wand_device_controller.play_spell_cast_cue(wand.id, has_sufficient_level)

    def _get_wizard_level(self, wand_id: str) -> WizardLevelType:
        return self._settings.wand_levels.get(wand_id, WizardLevelType.BEGINNER)

    def _has_sufficient_level(self, wizard_level: WizardLevelType, spell_level: WizardLevelType) -> bool:
        if wizard_level == WizardLevelType.BEGINNER and spell_level != WizardLevelType.BEGINNER:
            return False

        if wizard_level == WizardLevelType.INTERMEDIATE and spell_level == WizardLevelType.ADVANCED:
            return False

        return True
