from classification.curves import is_curve_180_cw_start_n, is_curve_270_cw_start_w
from classification.directions import has_azimuth_n
from detection.gesture import Gesture


def is_p(g: Gesture) -> bool:
    g1, g2 = g.split(0.25)

    part1 = has_azimuth_n(g1.azimuth)
    part2a = is_curve_270_cw_start_w(g2)
    part2b = is_curve_180_cw_start_n(g2)

    # print(f"R analysis| part 1: {part1}, part 2a: {part2a}, part 2b: {part2b}")

    return part1 and (part2a or part2b)
