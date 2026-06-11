from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from motion.configuration.motion_processor_settings import MotionProcessorSettings


@dataclass
class MotionSettings(SettingsBase):
    processor: MotionProcessorSettings
