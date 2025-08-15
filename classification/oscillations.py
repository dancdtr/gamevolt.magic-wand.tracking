from typing import Iterable

from classification.utils import matches_extrema
from gamevolt.maths.azimuth import Azimuth
from gamevolt.maths.extremum import Extremum

# =========================================
# Oscillations
# =========================================


def is_oscillation(extrema: Iterable[Extremum], azimuths: Iterable[Azimuth]) -> bool:
    target_extrema = (Extremum.from_azimuth(azimuth) for azimuth in azimuths)
    return matches_extrema(extrema, *target_extrema)
