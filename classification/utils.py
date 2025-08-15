from typing import Iterable

from classification.extremum import Extremum
from detection.gesture import Gesture
from detection.turn import TurnType
from gamevolt.iterables.iter_tools import equals


def matches_x_extrema(g: Gesture, *targets: Extremum) -> bool:
    return matches_extrema(g.iter_x_extrema(), *targets)


def matches_y_extrema(g: Gesture, *targets: Extremum) -> bool:
    return matches_extrema(g.iter_y_extrema(), *targets)


def matches_extrema(extrema: Iterable[Extremum], *targets: Extremum) -> bool:
    return equals(extrema, targets)


def matches_x_turn_types(g: Gesture, *turn_types: TurnType) -> bool:
    return matches_turn_types(g.iter_x_turn_types(), *turn_types)


def matches_y_turn_types(g: Gesture, *turn_types: TurnType) -> bool:
    return matches_turn_types(g.iter_y_turn_types(), *turn_types)


def matches_turn_types(turn_types: Iterable[TurnType], *targets: TurnType) -> bool:
    return equals(turn_types, targets)
