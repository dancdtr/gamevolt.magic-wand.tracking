from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from classification.lines import is_line_ne, is_line_nw, is_line_se, is_line_sw
from detection.gesture import Gesture


class IntercardinalClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.LINE_NE: is_line_ne,
            GestureType.LINE_SE: is_line_se,
            GestureType.LINE_SW: is_line_sw,
            GestureType.LINE_NW: is_line_nw,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
