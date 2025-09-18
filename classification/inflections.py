from gestures.gesture import Gesture
from gestures.turn_event import TurnEvent
from gestures.turn_type import TurnType


# =========================================
# Start Inflections
# =========================================
def starts_with_turn_type_n2s(g: Gesture) -> bool:
    return _starts_with_turn_point(g, TurnType.N2S)


def starts_with_turn_type_e2w(g: Gesture) -> bool:
    return _starts_with_turn_point(g, TurnType.E2W)


def starts_with_turn_type_s2n(g: Gesture) -> bool:
    return _starts_with_turn_point(g, TurnType.S2N)


def starts_with_turn_type_w2e(g: Gesture) -> bool:
    return _starts_with_turn_point(g, TurnType.W2E)


def starts_with_x_turn_type_e2w(g: Gesture) -> bool:
    return _starts_with_x_turn_point(g, TurnType.E2W)


def starts_with_x_turn_type_w2e(g: Gesture) -> bool:
    return _starts_with_x_turn_point(g, TurnType.W2E)


def starts_with_y_turn_type_n2s(g: Gesture) -> bool:
    return _starts_with_y_turn_point(g, TurnType.N2S)


def starts_with_y_turn_type_s2n(g: Gesture) -> bool:
    return _starts_with_y_turn_point(g, TurnType.S2N)


# =========================================
# End Inflections
# =========================================
def ends_with_turn_type_n2s(g: Gesture) -> bool:
    return _ends_with_turn_point(g, TurnType.N2S)


def ends_with_turn_type_e2w(g: Gesture) -> bool:
    return _ends_with_turn_point(g, TurnType.E2W)


def ends_with_turn_type_s2n(g: Gesture) -> bool:
    return _ends_with_turn_point(g, TurnType.S2N)


def ends_with_turn_type_w2e(g: Gesture) -> bool:
    return _ends_with_turn_point(g, TurnType.W2E)


def ends_with_x_turn_type_e2w(g: Gesture) -> bool:
    return _ends_with_x_turn_point(g, TurnType.E2W)


def ends_with_x_turn_type_w2e(g: Gesture) -> bool:
    return _ends_with_x_turn_point(g, TurnType.W2E)


def ends_with_y_turn_type_n2s(g: Gesture) -> bool:
    return _ends_with_y_turn_point(g, TurnType.N2S)


def ends_with_y_turn_type_s2n(g: Gesture) -> bool:
    return _ends_with_y_turn_point(g, TurnType.S2N)


# =========================================
# Utils
# =========================================
def _starts_with_turn_point(g: Gesture, type: TurnType) -> bool:
    return is_turn_type(g.first_turn_event, type)


def _starts_with_x_turn_point(g: Gesture, type: TurnType) -> bool:
    return is_turn_type(g.first_x_turn_event, type)


def _starts_with_y_turn_point(g: Gesture, type: TurnType) -> bool:
    return is_turn_type(g.first_y_turn_event, type)


def _ends_with_turn_point(g: Gesture, type: TurnType) -> bool:
    return is_turn_type(g.last_turn_event, type)


def _ends_with_x_turn_point(g: Gesture, type: TurnType) -> bool:
    return is_turn_type(g.last_x_turn_event, type)


def _ends_with_y_turn_point(g: Gesture, type: TurnType) -> bool:
    return is_turn_type(g.last_y_turn_event, type)


def is_turn_type(turn: TurnEvent | None, type: TurnType) -> bool:
    return turn is not None and turn.type is type
