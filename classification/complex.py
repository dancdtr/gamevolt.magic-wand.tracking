from collections.abc import Callable

from classification.arcs import is_arc_360_ccw_start_e, is_arc_360_ccw_start_n, is_arc_360_ccw_start_s, is_arc_360_ccw_start_w
from classification.directions import (
    InterCardinalDirection,
    is_moving_e,
    is_moving_n,
    is_moving_ne,
    is_moving_nw,
    is_moving_s,
    is_moving_se,
    is_moving_sw,
    is_moving_w,
)
from classification.flicks import Rotation
from gestures.gesture import Gesture

_LOOP_START = 0.3
_LOOP_END = 0.75

type LoopFunc = Callable[[Gesture], bool]

_LINE_LOOKUP: dict[InterCardinalDirection, LoopFunc] = {
    InterCardinalDirection.N : is_moving_s,
    InterCardinalDirection.E: is_moving_w,
    InterCardinalDirection.S : is_moving_n,
    InterCardinalDirection.W : is_moving_e,
    InterCardinalDirection.NE : is_moving_sw,
    InterCardinalDirection.SE : is_moving_nw,
    InterCardinalDirection.SW : is_moving_ne,
    InterCardinalDirection.NW : is_moving_se,
}

_CW_360_LOOPS: dict[InterCardinalDirection, LoopFunc] = {
    InterCardinalDirection.N : is_arc_360_ccw_start_e,
    InterCardinalDirection.E : is_arc_360_ccw_start_s,
    InterCardinalDirection.S : is_arc_360_ccw_start_w,
    InterCardinalDirection.W : is_arc_360_ccw_start_n,
    InterCardinalDirection.NE : is_arc_360_ccw_start_e,
    InterCardinalDirection.SE : is_arc_360_ccw_start_s,
    InterCardinalDirection.SE : is_arc_360_ccw_start_w,
    InterCardinalDirection.NW : is_arc_360_ccw_start_n,
}

_CCW_360_LOOPS: dict[InterCardinalDirection, LoopFunc] = {
    InterCardinalDirection.N : is_arc_360_ccw_start_e,
    InterCardinalDirection.E : is_arc_360_ccw_start_s,
    InterCardinalDirection.S : is_arc_360_ccw_start_w,
    InterCardinalDirection.W : is_arc_360_ccw_start_n,
    InterCardinalDirection.NE : is_arc_360_ccw_start_e,
    InterCardinalDirection.SE : is_arc_360_ccw_start_s,
    InterCardinalDirection.SE : is_arc_360_ccw_start_w,
    InterCardinalDirection.NW : is_arc_360_ccw_start_n,
}

# A loop is a straight line -> arc -> straight line
# loop 360 lines start and end straight lines have the same direction

# =========================================
# Loop CW
# =========================================



# =========================================
# Loop CCW
# =========================================

def is_loop_ccw_360_start_n(g: Gesture) -> bool:
    return _is_loop_360_ccw(g, InterCardinalDirection.N)

def is_loop_ccw_360_start_ne(g: Gesture) -> bool:
    return _is_loop_360_ccw(g, InterCardinalDirection.NE)

def is_loop_ccw_360_start_e(g: Gesture) -> bool:
    return _is_loop_360_ccw(g, InterCardinalDirection.E)

def is_loop_ccw_360_start_se(g: Gesture) -> bool:
    return _is_loop_360_ccw(g, InterCardinalDirection.SE)

def is_loop_ccw_360_start_s(g: Gesture) -> bool:
    return _is_loop_360_ccw(g, InterCardinalDirection.S)

def is_loop_ccw_360_start_sw(g: Gesture) -> bool:
    return _is_loop_360_ccw(g, InterCardinalDirection.SW)

def is_loop_ccw_360_start_w(g: Gesture) -> bool:
    start, middle = g.split(_LOOP_START)
    _, end = g.split(_LOOP_END)

    a = is_moving_e(start) or is_moving_s(start)
    b = is_arc_360_ccw_start_w(middle)
    c = is_moving_e(end) or is_moving_s(end)

    print(f"Is looper: {a ,b, c}")

    return a and b and c

    return _is_loop_360_ccw(g, InterCardinalDirection.W)

def is_loop_ccw_360_start_nw(g: Gesture) -> bool:
    return _is_loop_360_ccw(g, InterCardinalDirection.NW)


# =========================================
# Utils
# =========================================

def _is_loop_360_cw(g: Gesture, start_direction: InterCardinalDirection) -> bool:
    return _is_loop_360(g, start_direction, Rotation.CW)

def _is_loop_360_ccw(g: Gesture, start_direction: InterCardinalDirection) -> bool:
    return _is_loop_360(g, start_direction, Rotation.CCW)

def _is_loop_360(g: Gesture, start_direction: InterCardinalDirection, rotation: Rotation) -> bool:
    line_func = _LINE_LOOKUP[start_direction]
    
    if rotation is Rotation.CW:
        loop_func =_CW_360_LOOPS[start_direction]
    elif rotation is Rotation.CCW:
        loop_func =_CCW_360_LOOPS[start_direction]
    else:
        raise ValueError(f"No loop defined for direction: '{rotation.name}'!")
    
    g_line_1 = line_func(g)
    loop = loop_func(g)
    g_line_2 =  line_func(g)

    print(f"is loop: {g_line_1, loop, g_line_2}")

    return g_line_1 and loop and g_line_2



# def is_loop_ccw_360_start_nw(g: Gesture) -> bool:
#     start, middle = g.split(_LOOP_START)
#     _, end = g.split(_LOOP_END)

#     a = is_moving_e(start) or is_moving_s(start)
#     b = is_arc_360_ccw_start_w(middle)
#     c = is_moving_e(end) or is_moving_s(end)

#     print(f"Is looper: {a ,b, c}")

#     return a and b and c
