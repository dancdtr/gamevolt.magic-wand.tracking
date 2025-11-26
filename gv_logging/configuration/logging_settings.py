# shim for incompatible GV logging module settings
from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class LoggingSettings(SettingsBase):
    file_path: str
    minimum_level: str
