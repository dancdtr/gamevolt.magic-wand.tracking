from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class MouseSettings(SettingsBase):
    sample_frequency: int
    invert_x: bool
    invert_y: bool
