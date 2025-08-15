from enum import Enum, auto


class TurnType(Enum):
    N2S = auto()
    E2W = auto()
    S2N = auto()
    W2E = auto()

    # axis predicates
    def in_x(self) -> bool:
        T = type(self)
        return self is T.W2E or self is T.E2W

    def in_y(self) -> bool:
        T = type(self)
        return self is T.N2S or self is T.S2N
