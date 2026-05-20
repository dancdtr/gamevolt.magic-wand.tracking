from enum import Enum, auto


class SpellResponseType(Enum):
    FAIL = auto()
    OK = auto()
    GOOD = auto()
    BETTER = auto()
    BEST = auto()
