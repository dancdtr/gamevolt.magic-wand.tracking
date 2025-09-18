from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from classification.lines import is_line_ene, is_line_ese, is_line_nne, is_line_nnw, is_line_sse, is_line_ssw, is_line_wnw, is_line_wsw
from gestures.gesture import Gesture


class SubIntercardinalClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.LINE_NNE: is_line_nne,
            GestureType.LINE_ENE: is_line_ene,
            GestureType.LINE_ESE: is_line_ese,
            GestureType.LINE_SSE: is_line_sse,
            GestureType.LINE_SSW: is_line_ssw,
            GestureType.LINE_WSW: is_line_wsw,
            GestureType.LINE_WNW: is_line_wnw,
            GestureType.LINE_NNW: is_line_nnw,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
