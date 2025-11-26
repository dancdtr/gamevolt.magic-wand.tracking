from dataclasses import dataclass


@dataclass
class SpellMatcherSettings:
    relative_tolerance: float = 0.15
    minimum_total_distance: float = 0.3
    check_distance: bool = False
