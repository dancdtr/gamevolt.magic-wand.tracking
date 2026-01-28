from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class MotionPhaseTrackerSettings(SettingsBase):
    speed_start: float
    speed_stop: float

    # dwell to enter MOVING once above speed_start
    min_state_duration: float

    # still-episode thresholds (total time since still began)
    min_paused_duration: float  # eg 0.3
    min_holding_duration: float  # eg 0.8
    min_stopped_duration: float  # eg 1.3
