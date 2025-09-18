from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from classification.sines import (
    is_wave_negative_sine_e_360,
    is_wave_negative_sine_n_360,
    is_wave_negative_sine_s_360,
    is_wave_negative_sine_w_360,
    is_wave_sine_e_360,
    is_wave_sine_n_360,
    is_wave_sine_s_360,
    is_wave_sine_w_360,
)
from gestures.gesture import Gesture


class WaveSine360Classifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.WAVE_SINE_360_N: is_wave_sine_n_360,
            GestureType.WAVE_SINE_360_E: is_wave_sine_e_360,
            GestureType.WAVE_SINE_360_S: is_wave_sine_s_360,
            GestureType.WAVE_SINE_360_W: is_wave_sine_w_360,
            GestureType.WAVE_NEGATIVE_SINE_360_N: is_wave_negative_sine_n_360,
            GestureType.WAVE_NEGATIVE_SINE_360_E: is_wave_negative_sine_e_360,
            GestureType.WAVE_NEGATIVE_SINE_360_S: is_wave_negative_sine_s_360,
            GestureType.WAVE_NEGATIVE_SINE_360_W: is_wave_negative_sine_w_360,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
