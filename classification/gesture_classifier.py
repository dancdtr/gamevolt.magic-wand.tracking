from collections.abc import Callable
from enum import Enum, auto
from typing import Iterable

from classification.classifiers.classifier import Classifier
from classification.classifiers.gesture_classifier_mask import GestureClassifierMask
from classification.classifiers.lines.cardinal_classifier import CardinalClassifier
from classification.classifiers.lines.intercardinal_classifier import IntercardinalClassifier
from classification.classifiers.lines.secondary_intercardinal_classifier import SecondaryIntercardinalClassifier
from classification.gesture_type import GestureType
from classification.lines import (
    is_line_e,
    is_line_ene,
    is_line_ese,
    is_line_n,
    is_line_ne,
    is_line_nne,
    is_line_nnw,
    is_line_nw,
    is_line_s,
    is_line_se,
    is_line_sse,
    is_line_ssw,
    is_line_sw,
    is_line_w,
    is_line_wnw,
    is_line_wsw,
)
from detection.gesture import Gesture
from detection.turn import TurnType
from detection.turn_point import TurnPoint
from gamevolt.iterables.iter_tools import equals, equals_single, matches, matches_prefix
from gamevolt.maths.extremum import Extremum


class GestureClassifier:
    def __init__(self) -> None:
        self._classifiers: list[Classifier] = [
            CardinalClassifier(),
            IntercardinalClassifier(),
            SecondaryIntercardinalClassifier(),
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

        # check circles
        # if is_up_start_cw_circle(gesture):
        #     return GestureType.UP_START_CW_CIRCLE
        # if is_right_start_cw_circle(gesture):
        #     return GestureType.RIGHT_START_CW_CIRCLE
        # if is_down_start_cw_circle(gesture):
        #     return GestureType.DOWN_START_CW_CIRCLE
        # if is_left_start_cw_circle(gesture):
        #     return GestureType.LEFT_START_CW_CIRCLE
        # if is_up_start_ccw_circle(gesture):
        #     return GestureType.UP_START_CCW_CIRCLE
        # if is_right_start_ccw_circle(gesture):
        #     return GestureType.RIGHT_START_CCW_CIRCLE
        # if is_down_start_ccw_circle(gesture):
        #     return GestureType.DOWN_START_CCW_CIRCLE
        # if is_left_start_ccw_circle(gesture):
        #     return GestureType.LEFT_START_CCW_CIRCLE

        # check semi circles
        # if is_up_via_left_semi(gesture):
        #     return GestureType.UP_VIA_LEFT_SEMI
        # if is_up_via_right_semi(gesture):
        #     return GestureType.UP_VIA_RIGHT_SEMI
        # if is_right_via_up_semi(gesture):
        #     return GestureType.RIGHT_VIA_UP_SEMI
        # if is_right_via_down_semi(gesture):
        #     return GestureType.RIGHT_VIA_DOWN_SEMI
        # if is_down_via_right_semi(gesture):
        #     return GestureType.DOWN_VIA_RIGHT_SEMI
        # if is_down_via_left_semi(gesture):
        #     return GestureType.DOWN_VIA_LEFT_SEMI
        # if is_left_via_up_semi(gesture):
        #     return GestureType.LEFT_VIA_UP_SEMI
        # if is_left_via_down_semi(gesture):
        #     return GestureType.LEFT_VIA_DOWN_SEMI

        return gesture_type


def is_curve_relaxed(g: Gesture, *pattern: TurnType) -> bool:
    return matches_prefix(g.iter_turn_types(), pattern, allow_tail_missing=1, allow_tail_extra=0)


def is_up_start_cw_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN)


def is_up_start_cw_3_quarter_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT)


def is_right_start_cw_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT)


def is_down_start_cw_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP)


def is_left_start_cw_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT)


def is_up_start_ccw_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN)


def is_right_start_ccw_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT)


def is_down_start_ccw_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP)


def is_left_start_ccw_circle(g: Gesture) -> bool:
    return is_curve_relaxed(g, TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT)


def is_up_via_right_semi(g: Gesture) -> bool:
    return is_line_n(g) and is_right_left_curve(g)


def is_arc_half_cw_start_s(g: Gesture) -> bool:
    return is_line_n(g) and is_left_right_curve(g)


# def is_arc_half_cw_start_e(g: Gesture) -> bool:
#     return is_line_e(g) and is_up_down_curve(g)


def is_right_via_down_semi(g: Gesture) -> bool:
    return is_line_e(g) and is_down_up_curve(g)


def is_arc_half_cw_start_n(g: Gesture) -> bool:
    return is_line_s(g) and is_right_left_curve(g)


def is_down_via_left_semi(g: Gesture) -> bool:
    return is_line_s(g) and is_left_right_curve(g)


def is_left_via_up_semi(g: Gesture) -> bool:
    return is_line_w(g) and is_up_down_curve(g)


def is_arc_half_cw_start_e(g: Gesture) -> bool:
    return is_line_w(g) and is_down_up_curve(g)


def is_up_down_curve(g: Gesture) -> bool:
    return is_turn_point_type(g.last_y_turn_point, TurnType.UP_TO_DOWN) and matches(g.iter_y_extrema(), Extremum.Y_MAX, Extremum.Y_MIN)


def is_down_up_curve(g: Gesture) -> bool:
    return is_turn_point_type(g.last_y_turn_point, TurnType.DOWN_TO_UP) and matches(g.iter_y_extrema(), Extremum.Y_MIN, Extremum.Y_MAX)


def is_left_right_curve(g: Gesture) -> bool:
    return is_turn_point_type(g.last_x_turn_point, TurnType.LEFT_TO_RIGHT) and matches(g.iter_x_extrema(), Extremum.X_MIN, Extremum.X_MAX)


def is_right_left_curve(g: Gesture) -> bool:
    return is_turn_point_type(g.last_x_turn_point, TurnType.RIGHT_TO_LEFT) and matches(g.iter_x_extrema(), Extremum.X_MAX, Extremum.X_MIN)


def is_turn_point_type(turn_point: TurnPoint | None, turn_type: TurnType) -> bool:
    return turn_point is not None and turn_point.type == turn_type
