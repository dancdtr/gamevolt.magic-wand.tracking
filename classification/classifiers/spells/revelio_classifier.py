from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.crooks import is_crook_n_cw
from classification.gesture_type import GestureType
from classification.lines import is_line_se
from detection.gesture import Gesture


class RevelioClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.CROOK_N_CW: is_crook_n_cw,
            GestureType.LINE_SE: is_line_se,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
