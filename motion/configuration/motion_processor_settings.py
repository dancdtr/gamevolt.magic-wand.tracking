from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from motion.configuration.motion_phase_tracker_settings import MotionPhaseTrackerSettings


@dataclass
class MotionProcessorSettings(SettingsBase):

    # speed thresholds in normalised units per sec (x,y ∈ [0,1])
    # speed_start: float  # = 0.50  # commit MovementType.MOVING when speed >= start for dwell time
    # speed_stop: float  # = 0.20  # commit MovementType.STATIONARY when speed <= stop for dwell time
    # min_state_duration_s: float  # = 0.05  # motion state (moving vs stationary) dwell time
    # min_dir_duration_s: float  # = 0.06  # direction needs to be stable for this long before commit
    axis_deadband_per_s: float  # = 0.10  # ignore tiny axis components to reduce flicker at low speeds
    max_segment_points: int  # = 256  # cap how many raw points are stored per segment
    min_stopped_duration: float  # = 0.3
    phase_tracker: MotionPhaseTrackerSettings
