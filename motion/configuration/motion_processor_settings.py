from gamevolt.configuration.appsetting import appsetting
from motion.configuration.motion_phase_tracker_settings import MotionPhaseTrackerSettings


@appsetting
class MotionProcessorSettings:
    phase_tracker: MotionPhaseTrackerSettings

    # EMA factor applied to instantaneous speed before phase detection. 1.0 = no smoothing;
    # lower = more smoothing. Tames hand tremor that would otherwise spike past speed_start
    # and keep resetting the still-episode hold timers, delaying end-of-spell detection.
    speed_smoothing_alpha: float = 1.0

    # Spatial deadzone. If the integrated 2D path stays within `stillness_radius` over the
    # last `stillness_window_ms`, the wand is treated as still (speed forced to 0) regardless
    # of velocity. Tremor oscillates around a point — small net displacement — so this catches
    # end-of-spell that velocity thresholds miss. 0.0 = disabled.
    stillness_radius: float = 0.0
    stillness_window_ms: int = 200
