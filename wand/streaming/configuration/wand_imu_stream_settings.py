from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from wand.streaming.configuration.eliko_stream_settings import ElikoStreamSettings


@dataclass
class WandImuStreamSettings(SettingsBase):
    header_ttl_s: float
    eliko: ElikoStreamSettings | None
