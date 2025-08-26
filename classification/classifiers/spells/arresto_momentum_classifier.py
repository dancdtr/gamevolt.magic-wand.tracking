from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from classification.lines import is_line_nne, is_line_sse
from detection.gesture import Gesture


class ArrestoMomentumClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.LINE_NNE: is_line_nne,
            GestureType.LINE_SSE: is_line_sse,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
