from dataclasses import dataclass
from enum import Enum

from gamevolt.configuration.settings_base import SettingsBase
from wand.streaming.configuration.eliko_stream_settings import ElikoStreamSettings


class WandImuStreamMode(Enum):
    LINE_BASED = "line_based"
    ELIKO = "eliko"


@dataclass
class WandImuStreamSettings(SettingsBase):
    mode: WandImuStreamMode
    header_ttl_s: float
    eliko: ElikoStreamSettings | None
