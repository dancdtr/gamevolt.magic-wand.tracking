from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from motion.configuration.gesture_history_settings import GestureHistorySettings
from motion.configuration.motion_processor_settings import MotionProcessorSettings


@dataclass
class MotionSettings(SettingsBase):
    gesture_history: GestureHistorySettings
    processor: MotionProcessorSettings
