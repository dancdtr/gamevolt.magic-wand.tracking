from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from motion.configuration.motion_processor_settings import MotionProcessorSettings
from motion.gesture.configuration.gesture_history_settings import GestureHistorySettings


@dataclass
class MotionSettings(SettingsBase):
    gesture_history: GestureHistorySettings
    processor: MotionProcessorSettings
