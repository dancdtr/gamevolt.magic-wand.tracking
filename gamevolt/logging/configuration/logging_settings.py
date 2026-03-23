from __future__ import annotations

from dataclasses import dataclass
from time import strftime

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class LoggingSettings(SettingsBase):
    minimum_level: str = "INFORMATION"
    file_path: str = "GameVolt.Python.Logging.{timestamp}.log"

    FIELD_HANDLERS = {
        "file_path": lambda x: x.replace(
            "{timestamp}",
            strftime("%Y%m%d"),
        )
    }
