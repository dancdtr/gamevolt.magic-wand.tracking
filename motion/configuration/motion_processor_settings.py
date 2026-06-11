from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from motion.configuration.motion_phase_tracker_settings import MotionPhaseTrackerSettings


@dataclass
class MotionProcessorSettings(SettingsBase):
    phase_tracker: MotionPhaseTrackerSettings
