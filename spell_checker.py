from logging import Logger

from classification.classifiers.spells.spell import Spell
from classification.gesture_type import GestureType

_MAX_LENGTH = 10


class SpellChecker:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

        self._gesture_types: list[GestureType] = []

    def update_gestures(self, gesture_type: GestureType) -> None:
        if len(self._gesture_types) >= _MAX_LENGTH - 1:
            self._gesture_types.pop(0)

        self._gesture_types.append(gesture_type)

    def check(self, spell: Spell) -> bool:
        expected = spell.definition
        actual = self._gesture_types[-spell.length :]
        is_match = actual == expected

        self._logger.debug(f"Expected: {[gt.name for gt in expected]}")
        self._logger.debug(f"Actual: {[gt.name for gt in actual]}")
        self._logger.debug(f"Match: {'✅' if is_match else '❌'} ")

        return is_match

    def clear_gestures(self) -> None:
        self._gesture_types.clear()
