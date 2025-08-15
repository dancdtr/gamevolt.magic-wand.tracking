from __future__ import annotations

import re
from enum import StrEnum

from classification.gesture_components import GestureParts
from gamevolt.maths.axis import Axis
from gamevolt.maths.azimuth import Azimuth
from gamevolt.maths.dir import Dir
from gamevolt.maths.shape import Shape
from gamevolt.maths.span import Span
from gamevolt.maths.turn import Turn

# class GestureType(Enum):
#     NONE = "none"
#     UNKNOWN = "unknown"

#     UP = "up"
#     RIGHT = "right"
#     DOWN = "down"
#     LEFT = "left"

#     UP_RIGHT = "up_right"
#     DOWN_RIGHT = "down_right"
#     DOWN_LEFT = "down_left"
#     UP_LEFT = "up_left"

#     UP_VIA_RIGHT_SEMI = "up_via_right_semi"
#     UP_VIA_LEFT_SEMI = "up_via_left_semi"
#     DOWN_VIA_RIGHT_SEMI = "down_via_right_semi"
#     DOWN_VIA_LEFT_SEMI = "down_via_left_semi"

#     RIGHT_VIA_UP_SEMI = "right_via_up_semi"
#     LEFT_VIA_UP_SEMI = "left_via_up_semi"
#     RIGHT_VIA_DOWN_SEMI = "right_via_down_semi"
#     LEFT_VIA_DOWN_SEMI = "left_via_down_semi"

#     LEFT_START_CW_CIRCLE = "left_start_cw_circle"
#     UP_START_CW_CIRCLE = "up_start_cw_circle"
#     RIGHT_START_CW_CIRCLE = "right_start_cw_circle"
#     DOWN_START_CW_CIRCLE = "down_start_cw_circle"

#     LEFT_START_CCW_CIRCLE = "left_start_ccw_circle"
#     UP_START_CCW_CIRCLE = "up_start_ccw_circle"
#     RIGHT_START_CCW_CIRCLE = "right_start_ccw_circle"
#     DOWN_START_CCW_CIRCLE = "down_start_ccw_circle"

#     NNE = "nne"
#     ENE = "ene"
#     ESE = "ese"
#     SSE = "sse"
#     SSW = "ssw"
#     WSW = "wsw"
#     WNW = "wnw"
#     NNW = "nnw"


class GestureType(StrEnum):
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"

    # =========================================
    # 16-point compass directions
    # =========================================
    LINE_N = "LINE_N"
    LINE_E = "LINE_E"
    LINE_S = "LINE_S"
    LINE_W = "LINE_W"

    LINE_NE = "LINE_NE"
    LINE_SE = "LINE_SE"
    LINE_SW = "LINE_SW"
    LINE_NW = "LINE_NW"

    LINE_NNE = "NNE"
    LINE_ENE = "ENE"
    LINE_ESE = "ESE"
    LINE_SSE = "SSE"
    LINE_SSW = "SSW"
    LINE_WSW = "WSW"
    LINE_WNW = "WNW"
    LINE_NNW = "NNW"

    # =========================================
    # Half arcs
    # =========================================
    ARC_HALF_CW_START_N = "ARC_HALF_CW_START_N"
    ARC_HALF_CW_START_E = "ARC_HALF_CW_START_E"
    ARC_HALF_CW_START_S = "ARC_HALF_CW_START_S"
    ARC_HALF_CW_START_W = "ARC_HALF_CW_START_W"

    ARC_HALF_CCW_START_N = "ARC_HALF_CCW_START_N"
    ARC_HALF_CCW_START_E = "ARC_HALF_CCW_START_E"
    ARC_HALF_CCW_START_S = "ARC_HALF_CCW_START_S"
    ARC_HALF_CCW_START_W = "ARC_HALF_CCW_START_W"

    # =========================================
    # Three quarter arcs
    # =========================================
    ARC_THREE_QUARTER_CW_START_N = "ARC_THREE_QUARTER_CW_START_N"
    ARC_THREE_QUARTER_CW_START_E = "ARC_THREE_QUARTER_CW_START_E"
    ARC_THREE_QUARTER_CW_START_S = "ARC_THREE_QUARTER_CW_START_S"
    ARC_THREE_QUARTER_CW_START_W = "ARC_THREE_QUARTER_CW_START_W"

    ARC_THREE_QUARTER_CCW_START_N = "ARC_THREE_QUARTER_CCW_START_N"
    ARC_THREE_QUARTER_CCW_START_E = "ARC_THREE_QUARTER_CCW_START_E"
    ARC_THREE_QUARTER_CCW_START_S = "ARC_THREE_QUARTER_CCW_START_S"
    ARC_THREE_QUARTER_CCW_START_W = "ARC_THREE_QUARTER_CCW_START_W"

    # =========================================
    # Circles
    # =========================================
    CIRCLE_CW_START_N = "CIRCLE_CW_START_N"
    CIRCLE_CW_START_E = "CIRCLE_CW_START_E"
    CIRCLE_CW_START_S = "CIRCLE_CW_START_S"
    CIRCLE_CW_START_W = "CIRCLE_CW_START_W"

    CIRCLE_CCW_START_N = "CIRCLE_CCW_START_N"
    CIRCLE_CCW_START_E = "CIRCLE_CCW_START_E"
    CIRCLE_CCW_START_S = "CIRCLE_CCW_START_S"
    CIRCLE_CCW_START_W = "CIRCLE_CCW_START_W"

    # =========================================
    # Sine waves
    # =========================================
    WAVE_SINE_X_POS = "WAVE_SINE_X_POS"
    WAVE_SINE_X_NEG = "WAVE_SINE_X_NEG"
    WAVE_SINE_Y_POS = "WAVE_SINE_Y_POS"
    WAVE_SINE_Y_NEG = "WAVE_SINE_Y_NEG"

    def is_circle(self) -> bool:
        return self.value.startswith("CIRCLE_")

    def is_arc(self) -> bool:
        return self.value.startswith("ARC_")

    def is_line(self) -> bool:
        return self.value.startswith("LINE_")

    def is_wave(self) -> bool:
        return self.value.startswith("WAVE_")


# Registry for lookups: code -> enum
_GESTURE_REGISTRY: dict[str, GestureType] = {g.value: g for g in GestureType}

# ── Conversions & predicates ──────────────────────────────────────────────────


def try_gesture_type_from_parts(parts: GestureParts) -> GestureType | None:
    """Return a concrete enum if you’ve defined it; otherwise None."""
    return _GESTURE_REGISTRY.get(parts.code())


_GX = re.compile(
    r"""^
    (?:
        LINE_(?P<line>[NESW]{1,2}|NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW)
     |  CIRCLE_(?P<turn>CW|CCW)_START_(?P<cstart>[NESW]{1,2}|NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW)
     |  ARC_(?P<span>QUARTER|HALF|THREE_QUARTER)_(?P<aturn>CW|CCW)_START_(?P<astart>[NESW]{1,2}|NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW)
     |  (?P<wshape>WAVE_SINE|WAVE_COS)_(?P<waxis>X|Y)_(?P<wdir>POS|NEG)
    )$""",
    re.VERBOSE,
)


def parts_from_gesture_type(gt: GestureType) -> GestureParts:
    m = _GX.match(gt.value)
    if not m:
        return GestureParts(Shape.LINE, start=Azimuth.N)  # sensible fallback
    gd = m.groupdict()
    if gd["line"]:
        return GestureParts(Shape.LINE, start=Azimuth[gd["line"]])
    if gd["turn"]:
        return GestureParts(Shape.CIRCLE, start=Azimuth[gd["cstart"]], turn=Turn[gd["turn"]])
    if gd["span"]:
        return GestureParts(
            Shape.ARC,
            start=Azimuth[gd["astart"]],
            span=Span[gd["span"]],
            turn=Turn[gd["aturn"]],
        )
    # wave
    return GestureParts(
        Shape[gd["wshape"]],
        wave_axis=Axis[gd["waxis"]],
        wave_dir=Dir[gd["wdir"]],
    )
