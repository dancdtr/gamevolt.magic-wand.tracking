from dataclasses import dataclass


@dataclass(slots=True)
class MatchState:
    step_idx: int = 0

    matched_required: int = 0
    matched_optional: int = 0
    matched_pause: int = 0
    pause_duration_s: float = 0.0

    total_duration_s: float = 0.0
    filler_duration_s: float = 0.0

    total_distance: float = 0.0

    group_distance: list[float] | None = None
    group_duration_s: list[float] | None = None
    group_steps_matched: list[int] | None = None

    used_min_idx: int | None = None
    used_max_idx: int | None = None
