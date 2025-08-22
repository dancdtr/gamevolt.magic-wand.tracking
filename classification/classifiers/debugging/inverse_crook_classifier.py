from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.crooks import (
    is_inverse_crook_ccw_e,
    is_inverse_crook_ccw_n,
    is_inverse_crook_ccw_s,
    is_inverse_crook_ccw_w,
    is_inverse_crook_cw_e,
    is_inverse_crook_cw_n,
    is_inverse_crook_cw_s,
    is_inverse_crook_cw_w,
)
from classification.gesture_type import GestureType
from detection.gesture import Gesture


class InverseCrookClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.INVERSE_CROOK_N_CW: is_inverse_crook_cw_n,
            GestureType.INVERSE_CROOK_E_CW: is_inverse_crook_cw_e,
            GestureType.INVERSE_CROOK_S_CW: is_inverse_crook_cw_s,
            GestureType.INVERSE_CROOK_W_CW: is_inverse_crook_cw_w,
            GestureType.INVERSE_CROOK_N_CCW: is_inverse_crook_ccw_n,
            GestureType.INVERSE_CROOK_E_CCW: is_inverse_crook_ccw_e,
            GestureType.INVERSE_CROOK_S_CCW: is_inverse_crook_ccw_s,
            GestureType.INVERSE_CROOK_W_CCW: is_inverse_crook_ccw_w,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
