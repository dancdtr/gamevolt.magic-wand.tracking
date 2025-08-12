from enum import Enum


class GestureType(Enum):
    NONE = "none"
    UNKNOWN = "unknown"

    UP = "up"
    RIGHT = "right"
    DOWN = "down"
    LEFT = "left"

    UP_RIGHT = "up_right"
    DOWN_RIGHT = "down_right"
    DOWN_LEFT = "down_left"
    UP_LEFT = "up_left"

    UP_RIGHT_SEMI = "up_right_semi"
    UP_LEFT_SEMI = "up_left_semi"
    DOWN_RIGHT_SEMI = "down_right_semi"
    DOWN_LEFT_SEMI = "down_left_semi"

    RIGHT_UP_SEMI = "right_up_semi"
    LEFT_UP_SEMI = "left_up_semi"
    RIGHT_DOWN_SEMI = "right_down_semi"
    LEFT_DOWN_SEMI = "left_down_semi"
