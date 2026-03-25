from __future__ import annotations

from logging import Logger

from show_system.show_system_controller import ShowSystemController
from show_system.wizard_level import WizardLevel
from spell_cues.configuration.wand_spell_cue_controller_settings import WandSpellCueControllerSettings
from spells.spell_type import SpellType
from wand.tracked_wand import TrackedWand
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_device_controller import WandDeviceController
from zones.zone import Zone

SPELL_REQUIREMENTS: dict[SpellType, WizardLevel] = {
    SpellType.RICTUSEMPRA: WizardLevel.BEGINNER,
    SpellType.REPARO: WizardLevel.BEGINNER,
    SpellType.PEPPER_BREATH: WizardLevel.INTERMEDIATE,
    SpellType.APARECIUM: WizardLevel.INTERMEDIATE,
    SpellType.CANTIS: WizardLevel.ADVANCED,
}


class WandSpellCueController:
    def __init__(
        self,
        logger: Logger,
        settings: WandSpellCueControllerSettings,
        tracked_wand_manager: TrackedWandManager,
        wand_device_controller: WandDeviceController,
        show_system_controller: ShowSystemController,
    ) -> None:
        self._show_system_controller = show_system_controller
        self._wand_device_controller = wand_device_controller
        self._tracked_wand_manager = tracked_wand_manager
        self._settings = settings
        self._logger = logger

    def start(self) -> None:
        self._tracked_wand_manager.spell_cast.subscribe(self._on_spell_cast)

    def stop(self) -> None:
        self._tracked_wand_manager.spell_cast.unsubscribe(self._on_spell_cast)

    def _on_spell_cast(self, wand: TrackedWand, zone: Zone, spell_type: SpellType) -> None:
        wizard_level = self._get_wizard_level(wand.id)
        self._show_system_controller.play_spell(spell_type, wizard_level)

        spell_level = SPELL_REQUIREMENTS.get(spell_type, WizardLevel.BEGINNER)

        has_sufficient_level = self._has_sufficient_level(wizard_level, spell_level)
        cast_message = f"{'successfully cast' if has_sufficient_level else 'under cast'}"
        self._logger.debug(
            f"'{wizard_level.name.upper()}' wizard with wand ({wand.id}) {cast_message} '{spell_level.name}' spell '{spell_type.name}'."
        )
        self._wand_device_controller.play_spell_cast_cue(wand.id, has_sufficient_level)

    def _get_wizard_level(self, wand_id: str) -> WizardLevel:
        return self._settings.wand_levels.get(wand_id, WizardLevel.BEGINNER)

    def _has_sufficient_level(self, wizard_level: WizardLevel, spell_level: WizardLevel) -> bool:
        if wizard_level == WizardLevel.BEGINNER and spell_level != WizardLevel.BEGINNER:
            return False

        if wizard_level == WizardLevel.INTERMEDIATE and spell_level == WizardLevel.ADVANCED:
            return False

        return True
