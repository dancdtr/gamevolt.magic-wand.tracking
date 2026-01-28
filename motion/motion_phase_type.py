from enum import Enum, auto


class MotionPhaseType(Enum):
    NONE = auto()
    MOVING = auto()
    PAUSED = auto()
    HOLDING = auto()
    STOPPED = auto()
