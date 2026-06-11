from gamevolt.configuration.appsetting import appsetting
from motion.configuration.motion_phase_tracker_settings import MotionPhaseTrackerSettings


@appsetting
class MotionProcessorSettings:
    phase_tracker: MotionPhaseTrackerSettings
