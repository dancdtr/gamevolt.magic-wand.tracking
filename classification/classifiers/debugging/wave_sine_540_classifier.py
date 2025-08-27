from typing import Callable

from classification.classifiers.classifier import Classifier
from classification.gesture_type import GestureType
from classification.sines import (
    is_wave_negative_sine_e_540,
    is_wave_negative_sine_n_540,
    is_wave_negative_sine_s_540,
    is_wave_negative_sine_w_540,
    is_wave_sine_e_540,
    is_wave_sine_n_540,
    is_wave_sine_s_540,
    is_wave_sine_w_540,
)
from detection.gesture import Gesture


class WaveSine540Classifier(Classifier):
    def __init__(self) -> None:
        self._classifier_funcs: dict[GestureType, Callable[[Gesture], bool]] = {
            GestureType.WAVE_SINE_540_N: is_wave_sine_n_540,
            GestureType.WAVE_SINE_540_E: is_wave_sine_e_540,
            GestureType.WAVE_SINE_540_S: is_wave_sine_s_540,
            GestureType.WAVE_SINE_540_W: is_wave_sine_w_540,
            GestureType.WAVE_NEGATIVE_SINE_540_N: is_wave_negative_sine_n_540,
            GestureType.WAVE_NEGATIVE_SINE_540_E: is_wave_negative_sine_e_540,
            GestureType.WAVE_NEGATIVE_SINE_540_S: is_wave_negative_sine_s_540,
            GestureType.WAVE_NEGATIVE_SINE_540_W: is_wave_negative_sine_w_540,
        }

    @property
    def get_classifier_funcs(self) -> dict[GestureType, Callable[[Gesture], bool]]:
        return self._classifier_funcs
