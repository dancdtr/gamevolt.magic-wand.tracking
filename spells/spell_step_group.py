from dataclasses import dataclass

from spells.spell_step import SpellStep


@dataclass(frozen=True)
class SpellStepGroup:
    name: str
    steps: list[SpellStep]
    relative_duration: float
    relative_distance: float
    min_steps: int = 0

    # Repeated motif support: the step list is materialised between repeat_min and repeat_max
    # times during matching. The matcher tries each count (high → low) and returns the first hit.
    # Defaults to 1/1 = "do this group exactly once" (legacy behaviour).
    repeat_min: int = 1
    repeat_max: int = 1

    def __post_init__(self) -> None:
        if self.repeat_min < 1 or self.repeat_max < self.repeat_min:
            raise ValueError(
                f"SpellStepGroup '{self.name}': require 1 <= repeat_min <= repeat_max "
                f"(got {self.repeat_min}, {self.repeat_max})"
            )
