from dataclasses import dataclass

from anchor_area.configuration.anchor_area_settings import AnchorAreaSettings
from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class AnchorAreaManagerSettings(SettingsBase):
    anchor_areas: list[AnchorAreaSettings]
