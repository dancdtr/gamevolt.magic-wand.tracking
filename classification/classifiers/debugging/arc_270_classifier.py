from typing import Callable

from classification.arcs import (
    is_arc_270_ccw_start_e,
    is_arc_270_ccw_start_n,
    is_arc_270_ccw_start_s,
    is_arc_270_ccw_start_w,
    is_arc_270_cw_start_e,
    is_arc_270_cw_start_n,
    is_arc_270_cw_start_s,
    is_arc_270_cw_start_w,
)
from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from gestures.gesture import Gesture


class Arc270Classifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.ARC_270_CW_START_N: is_arc_270_cw_start_n,
            GestureType.ARC_270_CW_START_E: is_arc_270_cw_start_e,
            GestureType.ARC_270_CW_START_S: is_arc_270_cw_start_s,
            GestureType.ARC_270_CW_START_W: is_arc_270_cw_start_w,
            GestureType.ARC_270_CCW_START_N: is_arc_270_ccw_start_n,
            GestureType.ARC_270_CCW_START_E: is_arc_270_ccw_start_e,
            GestureType.ARC_270_CCW_START_S: is_arc_270_ccw_start_s,
            GestureType.ARC_270_CCW_START_W: is_arc_270_ccw_start_w,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
