from abc import ABC, abstractmethod
from typing import Callable

from classification.classifiers.gesture_classifier_mask import GestureClassifierMask
from classification.gesture_type import GestureType
from detection.gesture import Gesture


class Classifier(ABC):
    @property
    @abstractmethod
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]: ...

    def classify(self, gesture: Gesture, mask: GestureClassifierMask | None = None) -> GestureType:
        if mask is None:
            return self._classify_any(gesture)

        for target in mask.target_gesture_types:
            classifier_func = self._get_classifier_func(target)

            if classifier_func is None:
                return GestureType.UNKNOWN

            if classifier_func(gesture):
                return target

        return GestureType.UNKNOWN

    def _classify_any(self, gesture: Gesture) -> GestureType:
        for gesture_type, classifier_func in self.get_classifier_funcs.items():
            if classifier_func(gesture):
                return gesture_type

        return GestureType.UNKNOWN

    def _get_classifier_func(self, type: GestureType) -> Callable[[Gesture], bool] | None:
        return self.get_classifier_funcs.get(type, None)
