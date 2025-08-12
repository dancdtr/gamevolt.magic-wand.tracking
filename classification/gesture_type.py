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

    UP_VIA_RIGHT_SEMI = "up_via_right_semi"
    UP_VIA_LEFT_SEMI = "up_via_left_semi"
    DOWN_VIA_RIGHT_SEMI = "down_via_right_semi"
    DOWN_VIA_LEFT_SEMI = "down_via_left_semi"

    RIGHT_VIA_UP_SEMI = "right_via_up_semi"
    LEFT_VIA_UP_SEMI = "left_via_up_semi"
    RIGHT_VIA_DOWN_SEMI = "right_via_down_semi"
    LEFT_VIA_DOWN_SEMI = "left_via_down_semi"

    LEFT_START_CW_CIRCLE = "left_start_cw_circle"
    UP_START_CW_CIRCLE = "up_start_cw_circle"
    RIGHT_START_CW_CIRCLE = "right_start_cw_circle"
    DOWN_START_CW_CIRCLE = "down_start_cw_circle"

    LEFT_START_CCW_CIRCLE = "left_start_ccw_circle"
    UP_START_CCW_CIRCLE = "up_start_ccw_circle"
    RIGHT_START_CCW_CIRCLE = "right_start_ccw_circle"
    DOWN_START_CCW_CIRCLE = "down_start_ccw_circle"
