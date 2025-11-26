from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class MotionPhaseTrackerSettings(SettingsBase):
    speed_start: float = 0.50
    speed_stop: float = 0.20
    min_state_duration: float = 0.03
    min_stopped_duration: float = 0.03
