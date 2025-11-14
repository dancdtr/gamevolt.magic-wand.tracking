from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.visualisation.configuration.axes_settings import AxesSettings
from gamevolt.visualisation.configuration.label_settings import LabelSettings
from gamevolt.visualisation.configuration.visualiser_settings import VisualiserSettings
from visualisation.configuration.trail_settings import TrailSettings


@dataclass
class WandVisualiserSettings(SettingsBase):
    visualiser: VisualiserSettings
    label: LabelSettings
    axes: AxesSettings
    trail: TrailSettings
