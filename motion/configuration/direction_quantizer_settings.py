from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class DirectionQuantizerSettings(SettingsBase):
    speed_stop: float
    min_direction_duration: float
    axis_deadband_per_s: float
