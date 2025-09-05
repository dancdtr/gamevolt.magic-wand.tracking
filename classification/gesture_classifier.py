from logging import Logger

from classification.classifiers.classifier import Classifier
from classification.classifiers.classifier_2 import Classifier2
from classification.classifiers.debugging.arc_180_classifier import Arc180Classifier
from classification.classifiers.debugging.arc_270_classifier import Arc270Classifier
from classification.classifiers.debugging.arc_360_classifier import Arc360Classifier
from classification.classifiers.debugging.cardinal_classifier import CardinalClassifier
from classification.classifiers.debugging.crook_classifier import CrookClassifier
from classification.classifiers.debugging.hook_classifier import HookClassifier
from classification.classifiers.debugging.intercardinal_classifier import IntercardinalClassifier
from classification.classifiers.debugging.inverse_crook_classifier import InverseCrookClassifier
from classification.classifiers.debugging.inverse_hook_classifier import InverseHookClassifier
from classification.classifiers.debugging.sub_intercardinal_classifier import SubIntercardinalClassifier
from classification.classifiers.debugging.wave_sine_360_classifier import WaveSine360Classifier
from classification.classifiers.debugging.wave_sine_540_classifier import WaveSine540Classifier
from classification.classifiers.gesture_classifier_mask import GestureClassifierMask
from classification.classifiers.spells.spell import Spell
from classification.classifiers.spells.spell_factory import SpellFactory
from classification.gesture_type import GestureType
from detection.gesture import Gesture
from detection.gesture_func_provider import GestureFuncProvider
from spell_type import SpellType


class GestureClassifier:
    def __init__(self, logger: Logger, spell_book: SpellFactory, func_provider: GestureFuncProvider) -> None:
        self._logger = logger

        self._spell_book = spell_book
        self._func_provider = func_provider

        self._classifiers: list[Classifier] = [
            Arc360Classifier(),
            # Arc270Classifier(),
            # Arc180Classifier(),
            # SubIntercardinalClassifier(),
            # IntercardinalClassifier(),
            # CardinalClassifier(),
            # InverseCrookClassifier(),
            # CrookClassifier(),
            # HookClassifier(),
            # InverseHookClassifier(),
            # SilencioClassifier(),
            # LocomotorClassifier(),
            # ArrestoMomentumClassifier(),
            # WaveSine360Classifier(),
            # WaveSine540Classifier()
        ]

        self.current_spell: Spell | None = None

    def update_classifier(self, spell_type: SpellType) -> None:
        spell = self._spell_book.create(spell_type)
        self.current_spell = spell
        classifier = Classifier2(self._func_provider, spell.get_gestures)
        self._classifiers = [classifier]

    def classify(self, gesture: Gesture, mask: GestureClassifierMask | None = None) -> list[GestureType]:
        self._logger.debug(f"Extrema: {[e.type.name for e in gesture.extrema_events]}")
        self._logger.debug(f"X extrema: {[e.name for e in gesture.iter_x_extrema()]}")
        self._logger.debug(f"Y extrema: {[e.name for e in gesture.iter_y_extrema()]}")
        self._logger.debug(f"Turn points: {[tp.type.name for tp in gesture.turn_events]}")

        # print(is_p(gesture))

        gesture_types = []

        for classifier in self._classifiers:
            gesture_type = classifier.classify(gesture, mask)
            if gesture_type is not GestureType.UNKNOWN:
                gesture_types.append(gesture_type)

        if len(gesture_types) == 0:
            gesture_types.append(GestureType.UNKNOWN)

        return gesture_types
