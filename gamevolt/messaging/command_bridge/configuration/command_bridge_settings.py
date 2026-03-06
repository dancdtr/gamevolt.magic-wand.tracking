from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class CommandBridgeSettings(SettingsBase):
    repeat: int = 2
    allow_broadcast: bool = True
