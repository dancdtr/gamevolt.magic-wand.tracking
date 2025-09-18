from abc import ABC, abstractmethod
from typing import Callable

from classification.gesture_type import GestureType
from gestures.gesture import Gesture


class Classifier(ABC):
    @property
    @abstractmethod
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]: ...

    def classify(self, gesture: Gesture) -> GestureType:
        return self._classify_any(gesture)

    def _classify_any(self, gesture: Gesture) -> GestureType:
        for gesture_type, classifier_func in self.get_classifier_funcs.items():
            if classifier_func(gesture):
                return gesture_type

        return GestureType.UNKNOWN

    def _get_classifier_func(self, gesture_type: GestureType) -> Callable[[Gesture], bool] | None:
        return self.get_classifier_funcs.get(gesture_type, None)
