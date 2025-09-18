from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.crooks import (
    is_crook_e_ccw,
    is_crook_e_cw,
    is_crook_n_ccw,
    is_crook_n_cw,
    is_crook_s_ccw,
    is_crook_s_cw,
    is_crook_w_ccw,
    is_crook_w_cw,
)
from classification.gesture_type import GestureType
from gestures.gesture import Gesture


class CrookClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.CROOK_N_CW: is_crook_n_cw,
            GestureType.CROOK_E_CW: is_crook_e_cw,
            GestureType.CROOK_S_CW: is_crook_s_cw,
            GestureType.CROOK_W_CW: is_crook_w_cw,
            GestureType.CROOK_N_CCW: is_crook_n_ccw,
            GestureType.CROOK_E_CCW: is_crook_e_ccw,
            GestureType.CROOK_S_CCW: is_crook_s_ccw,
            GestureType.CROOK_W_CCW: is_crook_w_ccw,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
