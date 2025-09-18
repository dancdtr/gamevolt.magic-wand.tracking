from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from classification.lines import is_line_e, is_line_n, is_line_s, is_line_w
from gestures.gesture import Gesture


class CardinalClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.LINE_N: is_line_n,
            GestureType.LINE_E: is_line_e,
            GestureType.LINE_S: is_line_s,
            GestureType.LINE_W: is_line_w,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
