from logging import Logger

from classification.gesture_type import GestureType
from spell_type import SpellType


class SpellChecker:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

        self._gesture_types: list[GestureType] = []
        self._max_length = 10

    def update_gestures(self, gesture_type: GestureType) -> None:
        if len(self._gesture_types) >= self._max_length - 1:
            self._gesture_types.pop(0)

        self._gesture_types.append(gesture_type)

    def purge_gestures(self) -> None:
        self._gesture_types.clear()

    def check_spells(self) -> SpellType:
        if self.check_silencio():
            return SpellType.SILENCIO

        return SpellType.NONE

    def check_silencio(self) -> bool:
        actual = self._gesture_types[-2:]
        expected = [GestureType.ARC_180_CW_START_E, GestureType.LINE_S]

        return self._check_spell(expected, actual)

    def check_revelio(self) -> bool:
        actual = self._gesture_types[-2:]
        expected = [GestureType.CROOK_N_CW, GestureType.LINE_SE]

        return self._check_spell(expected, actual)

    def check_locomotor(self) -> bool:
        actual = self._gesture_types[-3:]
        expected = [GestureType.LINE_N, GestureType.LINE_SW, GestureType.LINE_E]

        return self._check_spell(expected, actual)

    def check_arresto_momentum(self) -> bool:
        actual = self._gesture_types[-4:]
        expected = [GestureType.LINE_NNE, GestureType.LINE_SSE, GestureType.LINE_NNE, GestureType.LINE_SSE]

        return self._check_spell(expected, actual)

    def _check_spell(self, expected: list[GestureType], actual: list[GestureType]) -> bool:

        self._logger.debug(f"A: {[gt.name for gt in actual]}")
        self._logger.debug(f"E: {[gt.name for gt in expected]}")

        match = actual == expected
        self._logger.debug(f"Match: {'✅' if match else '❌'} ")

        return match
