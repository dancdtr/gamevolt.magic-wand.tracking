from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from classification.hooks import (
    is_hook_e_ccw,
    is_hook_e_cw,
    is_hook_n_ccw,
    is_hook_n_cw,
    is_hook_s_ccw,
    is_hook_s_cw,
    is_hook_w_ccw,
    is_hook_w_cw,
)
from gestures.gesture import Gesture


class HookClassifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.HOOK_N_CW: is_hook_n_cw,
            GestureType.HOOK_E_CW: is_hook_e_cw,
            GestureType.HOOK_S_CW: is_hook_s_cw,
            GestureType.HOOK_W_CW: is_hook_w_cw,
            GestureType.HOOK_N_CCW: is_hook_n_ccw,
            GestureType.HOOK_E_CCW: is_hook_e_ccw,
            GestureType.HOOK_S_CCW: is_hook_s_ccw,
            GestureType.HOOK_W_CCW: is_hook_w_ccw,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
