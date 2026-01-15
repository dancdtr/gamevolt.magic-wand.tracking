# shim for incompatible GV logging module settings
from dataclasses import dataclass

from gamevolt_logging.configuration import LoggingSettings as GameVoltLoggingSettings

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class LoggingSettings(SettingsBase):
    file_path: str
    minimum_level: str

    def to_gamevolt_logging_settings(self) -> GameVoltLoggingSettings:
        return GameVoltLoggingSettings(
            file_path=self.file_path,
            minimum_level=self.minimum_level,
        )
