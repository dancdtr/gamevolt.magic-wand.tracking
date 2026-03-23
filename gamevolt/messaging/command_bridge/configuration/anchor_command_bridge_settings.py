from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class AnchorCommandBridgeSettings(SettingsBase):
    repeat: int
