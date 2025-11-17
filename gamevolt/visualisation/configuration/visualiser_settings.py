from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.visualisation.configuration.canvas_settings import CanvasSettings
from gamevolt.visualisation.configuration.preview_settings import RootSettings


@dataclass
class VisualiserSettings(SettingsBase):
    root: RootSettings
    canvas: CanvasSettings
