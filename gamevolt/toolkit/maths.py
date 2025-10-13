@staticmethod
def clamp(v: float, lower: float, upper: float) -> float:
    return lower if v < lower else upper if v > upper else v


def clamp01(v: float) -> float:
    return clamp(v, 0, 1)
