from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from visualisation.configuration.trail_settings import TrailColourSettings


@dataclass
class TrackedWandSettings(SettingsBase):
    id: str
    is_enabled: bool
    colour: TrailColourSettings
