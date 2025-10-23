from logging import Logger

from spells.library.spell_difficulty_type import SpellDifficultyType


class SpellDifficultyController:
    def __init__(self, logger: Logger, start_difficulty: SpellDifficultyType = SpellDifficultyType.FORGIVING) -> None:
        self._logger = logger

        self._difficulty = start_difficulty

    @property
    def difficulty(self) -> SpellDifficultyType:
        return self._difficulty

    def set_difficulty(self, difficulty: SpellDifficultyType) -> None:
        self._logger.info(f"⚠️ Setting spell casting difficulty to: '{difficulty.name.lower()}'.")
        self._difficulty = difficulty

    def toggle_difficulty(self) -> None:
        difficulty = SpellDifficultyType.STRICT if self._difficulty is SpellDifficultyType.FORGIVING else SpellDifficultyType.FORGIVING
        self.set_difficulty(difficulty)
