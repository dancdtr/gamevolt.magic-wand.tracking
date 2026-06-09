from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from wand.streaming.eliko.configuration.eliko_stream_settings import ElikoStreamSettings
from wand.streaming.eliko_single_anchor.configuration.eliko_single_anchor_stream_settings import (
    ElikoSingleAnchorStreamSettings,
)


@dataclass
class WandImuStreamSettings(SettingsBase):
    header_ttl_s: float
    eliko: ElikoStreamSettings | None
    eliko_single_anchor: ElikoSingleAnchorStreamSettings | None
