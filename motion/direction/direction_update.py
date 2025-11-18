from dataclasses import dataclass

from motion.direction.direction_type import DirectionType


@dataclass(frozen=True)
class DirectionUpdate:
    new_direction: DirectionType | None
