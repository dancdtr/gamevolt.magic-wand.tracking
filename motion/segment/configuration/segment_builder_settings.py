from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class SegmentBuilderSettings(SettingsBase):
    max_sample_count: int
