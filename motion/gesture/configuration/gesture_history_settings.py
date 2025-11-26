from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class GestureHistorySettings(SettingsBase):
    max_segments: int = 20
    max_age: float = 5.0
