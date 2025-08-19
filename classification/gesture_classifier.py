from classification.classifiers.arcs.arc_180_classifier import Arc180Classifier
from classification.classifiers.arcs.arc_270_classifier import Arc270Classifier
from classification.classifiers.arcs.arc_360_classifier import Arc360Classifier
from classification.classifiers.classifier import Classifier
from classification.classifiers.gesture_classifier_mask import GestureClassifierMask
from classification.classifiers.lines.cardinal_classifier import CardinalClassifier
from classification.classifiers.lines.intercardinal_classifier import IntercardinalClassifier
from classification.classifiers.lines.sub_intercardinal_classifier import SubIntercardinalClassifier
from classification.gesture_type import GestureType
from detection.gesture import Gesture


class GestureClassifier:
    def __init__(self) -> None:
        self._classifiers: list[Classifier] = [
            # Arc360Classifier(),
            # Arc270Classifier(),
            # Arc180Classifier(),
            SubIntercardinalClassifier(),
            # IntercardinalClassifier(),
            # CardinalClassifier(),
        ]

    def classify(self, gesture: Gesture, mask: GestureClassifierMask | None = None) -> GestureType:
        print(f"Extrema: {[e.name for e in gesture.extrema]}")
        print(f"X extrema: {[e.name for e in gesture.iter_x_extrema()]}")
        print(f"Y extrema: {[e.name for e in gesture.iter_y_extrema()]}")
        print(f"Turn points: {[tp.type.name for tp in gesture.turn_points]}")

        for classifier in self._classifiers:
            gesture_type = classifier.classify(gesture, mask)
            if gesture_type is not GestureType.UNKNOWN:
                return gesture_type

        return GestureType.UNKNOWN
