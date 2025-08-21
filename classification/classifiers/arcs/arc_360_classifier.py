from typing import Callable

from classification.arcs import (
    is_arc_360_ccw_start_e,
    is_arc_360_ccw_start_n,
    is_arc_360_ccw_start_s,
    is_arc_360_ccw_start_w,
    is_arc_360_cw_start_e,
    is_arc_360_cw_start_n,
    is_arc_360_cw_start_s,
    is_arc_360_cw_start_w,
)
from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from detection.gesture import Gesture


class Arc360Classifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.ARC_360_CW_START_N: is_arc_360_cw_start_n,
            GestureType.ARC_360_CW_START_E: is_arc_360_cw_start_e,
            GestureType.ARC_360_CW_START_S: is_arc_360_cw_start_s,
            GestureType.ARC_360_CW_START_W: is_arc_360_cw_start_w,
            GestureType.ARC_360_CCW_START_N: is_arc_360_ccw_start_n,
            GestureType.ARC_360_CCW_START_E: is_arc_360_ccw_start_e,
            GestureType.ARC_360_CCW_START_S: is_arc_360_ccw_start_s,
            GestureType.ARC_360_CCW_START_W: is_arc_360_ccw_start_w,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
