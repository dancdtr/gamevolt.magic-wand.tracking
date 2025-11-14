from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from preview.configuration.canvas_settings import CanvasSettings
from preview.configuration.label_settings import LabelSettings
from preview.configuration.preview_settings import RootSettings


@dataclass
class VisualiserSettings(SettingsBase):
    root: RootSettings
    canvas: CanvasSettings
    label: LabelSettings
