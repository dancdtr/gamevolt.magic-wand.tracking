from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from detection.gesture import Gesture
from detection.gesture_func_provider import GestureFuncProvider


class Classifier2(Classifier):
    def __init__(self, func_provider: GestureFuncProvider, types: list[GestureType]) -> None:
        self._types = types

        self._func_provider = func_provider
        self._identifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {type: func_provider.get(type) for type in types}

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._identifier_funcs
