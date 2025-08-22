from classification.classifiers.classifier import Classifier
from classification.classifiers.debugging.arc_180_classifier import Arc180Classifier
from classification.classifiers.debugging.arc_270_classifier import Arc270Classifier
from classification.classifiers.debugging.arc_360_classifier import Arc360Classifier
from classification.classifiers.debugging.cardinal_classifier import CardinalClassifier
from classification.classifiers.debugging.crook_classifier import CrookClassifier
from classification.classifiers.debugging.intercardinal_classifier import IntercardinalClassifier
from classification.classifiers.debugging.inverse_crook_classifier import InverseCrookClassifier
from classification.classifiers.debugging.sub_intercardinal_classifier import SubIntercardinalClassifier
from classification.classifiers.gesture_classifier_mask import GestureClassifierMask
from classification.classifiers.spells.revelio_classifier import RevelioClassifier
from classification.gesture_type import GestureType
from detection.gesture import Gesture


class GestureClassifier:
    def __init__(self) -> None:
        self._classifiers: list[Classifier] = [
            # Arc360Classifier(),
            # Arc270Classifier(),
            # Arc180Classifier(),
            # RevelioClassifier()
            InverseCrookClassifier()
            # CrookClassifier()
            # SubIntercardinalClassifier(),
            # IntercardinalClassifier(),
            # CardinalClassifier(),
        ]

    def classify(self, gesture: Gesture, mask: GestureClassifierMask | None = None) -> list[GestureType]:
        print(f"Extrema: {[e.type.name for e in gesture.extrema_events]}")
        print(f"X extrema: {[e.name for e in gesture.iter_x_extrema()]}")
        print(f"Y extrema: {[e.name for e in gesture.iter_y_extrema()]}")
        print(f"Turn points: {[tp.type.name for tp in gesture.turn_events]}")

        # print(is_p(gesture))

        gesture_types = []

        for classifier in self._classifiers:
            gesture_type = classifier.classify(gesture, mask)
            if gesture_type is not GestureType.UNKNOWN:
                gesture_types.append(gesture_type)

        if len(gesture_types) == 0:
            gesture_types.append(GestureType.UNKNOWN)

        return gesture_types
