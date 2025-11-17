from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class AxesSettings(SettingsBase):
    show_axes: bool
    colour: str
    width: int
