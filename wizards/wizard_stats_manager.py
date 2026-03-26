from logging import Logger

from wizards.configuration.wizard_stats_manager_settings import WizardStatsManagerSettings
from wizards.wizard_level_type import WizardLevelType


class WizardStatsManager:
    def __init__(self, logger: Logger, settings: WizardStatsManagerSettings) -> None:
        self._settings = settings
        self._logger = logger

        self._wizard_stats: dict[str, int] = {}

    def create_wizard_stats(self, wand_ids: list[str]) -> None:
        self._logger.info(f"Creating wizard stats for wands: {wand_ids}.")
        self._wizard_stats = {wand_id: 0 for wand_id in wand_ids}

    def get_wizard_level(self, wand_id: str) -> WizardLevelType:
        if wand_id not in self._wizard_stats.keys():
            self._logger.warning(f"No wizard level for wand ({wand_id})!")

        xp = self._wizard_stats.get(wand_id, 0)

        if xp >= self._settings.advanced_threshold:
            return WizardLevelType.ADVANCED
        elif xp >= self._settings.intermediate_threshold:
            return WizardLevelType.INTERMEDIATE
        else:
            return WizardLevelType.BEGINNER

    def on_spell_cast(self, wand_id: str) -> None:
        if wand_id not in self._wizard_stats.keys():
            self._logger.warning(f"No wizard level for wand ({wand_id})!")
            return

        self._wizard_stats[wand_id] += 1

    def reset(self) -> None:
        for k in self._wizard_stats.keys():
            self._wizard_stats[k] = 0
