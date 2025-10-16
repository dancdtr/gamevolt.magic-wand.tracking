from spells.library.spell_difficulty_type import SpellDifficultyType


class SpellDifficultyController:
    def __init__(self, start_difficulty: SpellDifficultyType = SpellDifficultyType.EASY) -> None:
        self._difficulty = start_difficulty

    @property
    def difficulty(self) -> SpellDifficultyType:
        return self._difficulty

    def set_difficulty(self, difficulty: SpellDifficultyType) -> None:
        print(f"Setting spell casting difficulty to: {difficulty}")
        self._difficulty = difficulty

    def toggle_difficulty(self) -> None:
        difficulty = SpellDifficultyType.HARD if self._difficulty is SpellDifficultyType.EASY else SpellDifficultyType.EASY
        self.set_difficulty(difficulty)
