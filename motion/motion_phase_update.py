from dataclasses import dataclass

from motion.motion_type import MotionPhaseType


@dataclass(frozen=True)
class MotionPhaseUpdate:
    new_phase: MotionPhaseType | None = None
    stop_started: bool = False
