from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.visualisation.configuration.root_settings import RootSettings
from gamevolt.visualisation.configuration.visualiser_settings import VisualiserSettings


@dataclass
class ZoneVisualiserSettings(SettingsBase):
    visualiser: VisualiserSettings
