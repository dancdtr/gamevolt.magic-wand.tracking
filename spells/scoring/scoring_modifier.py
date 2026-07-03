from enum import Enum, auto


class ScoringModifier(Enum):
    """Optional additive components of a cast score, each toggleable as a dev tool.

    Disabling one zeroes its contribution; the base (match accuracy × difficulty) and
    the gates are never affected. PITY gates the streak (pity) pass that lets a
    gate-passing cast reach its lowest tier on a failure streak.
    """

    XP = auto()
    CADENCE = auto()
    TEMPO = auto()
    PITY = auto()
