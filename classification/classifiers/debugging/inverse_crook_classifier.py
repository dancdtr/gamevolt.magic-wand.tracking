from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.crooks import (
    is_inverse_crook_e_ccw,
    is_inverse_crook_e_cw,
    is_inverse_crook_n_ccw,
    is_inverse_crook_n_cw,
    is_inverse_crook_s_ccw,
    is_inverse_crook_s_cw,
    is_inverse_crook_w_ccw,
    is_inverse_crook_w_cw,
)
from classification.gesture_type import GestureType
from gestures.gesture import Gesture


class InverseCrookClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.INVERSE_CROOK_N_CW: is_inverse_crook_n_cw,
            GestureType.INVERSE_CROOK_E_CW: is_inverse_crook_e_cw,
            GestureType.INVERSE_CROOK_S_CW: is_inverse_crook_s_cw,
            GestureType.INVERSE_CROOK_W_CW: is_inverse_crook_w_cw,
            GestureType.INVERSE_CROOK_N_CCW: is_inverse_crook_n_ccw,
            GestureType.INVERSE_CROOK_E_CCW: is_inverse_crook_e_ccw,
            GestureType.INVERSE_CROOK_S_CCW: is_inverse_crook_s_ccw,
            GestureType.INVERSE_CROOK_W_CCW: is_inverse_crook_w_ccw,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
