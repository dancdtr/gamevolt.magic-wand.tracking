from typing import Callable

from classification.arcs import is_arc_180_cw_start_e
from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from classification.lines import is_line_s
from detection.gesture import Gesture


class SilencioClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.ARC_180_CW_START_E: is_arc_180_cw_start_e,
            GestureType.LINE_S: is_line_s,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
