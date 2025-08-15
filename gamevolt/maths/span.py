from enum import Enum


class Span(Enum):
    QUARTER = 90
    HALF = 180
    THREE_QUARTER = 270
    FULL = 360  # rarely used directly; CIRCLE implies FULL
