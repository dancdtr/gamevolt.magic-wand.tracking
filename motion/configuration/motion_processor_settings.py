from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from motion.configuration.motion_phase_tracker_settings import MotionPhaseTrackerSettings
from motion.direction.configuration.direction_quantizer_settings import DirectionQuantizerSettings
from motion.segment.configuration.segment_builder_settings import SegmentBuilderSettings


@dataclass
class MotionProcessorSettings(SettingsBase):
    phase_tracker: MotionPhaseTrackerSettings
    direction_quantizer: DirectionQuantizerSettings
    segment_builder: SegmentBuilderSettings
