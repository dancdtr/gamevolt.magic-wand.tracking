from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class CanvasSettings(SettingsBase):
    background_colour: str
    highlight_thickness: int
