from vector_2 import Vector2


class IntercardinalClassifier:
    def __init__(self) -> None:
        pass

    def classify(self, points: list[Vector2]) -> str:
        v = Vector2.from_average(points)

        abs_x = abs(v.x)
        abs_y = abs(v.y)

        # 2) Decide intercardinal vs cardinal
        # If the two components are within, say, ±20%, treat as intercardinal
        INTERCARDINAL_RATIO = 0.65  # 80% ≤ min/max ≤ 1.25 → roughly “equal”
        direction: str

        if abs_x > 0 and abs_y > 0 and (min(abs_x, abs_y) / max(abs_x, abs_y) >= INTERCARDINAL_RATIO):
            # Intercardinal: both axes active and similar magnitude
            if v.x > 0 and v.y > 0:
                direction = "down-left"
            elif v.x > 0 and v.y < 0:
                direction = "up-left"
            elif v.x < 0 and v.y < 0:
                direction = "up-right"
            else:  # v.x < 0 and v.y > 0
                direction = "down-right"

        else:
            # Pure cardinal: pick the dominant axis
            if abs_x > abs_y:
                direction = "left" if v.x > 0 else "right"
            else:
                direction = "down" if v.y > 0 else "up"

        return direction
