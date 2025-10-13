from dataclasses import dataclass


@dataclass
class MotionProcessorSettings:
    # speed thresholds in normalised units per sec (x,y ∈ [0,1])
    speed_start: float = 0.50  # commit MovementType.MOVING when speed >= start for dwell time
    speed_stop: float = 0.20  # commit MovementType.STATIONARY when speed <= stop for dwell time

    min_dir_duration_s: float = 0.06  # direction needs to be stable for this long before commit
    min_state_duration_s: float = 0.05  # motion state (moving vs stationary) dwell time
    axis_deadband_per_s: float = 0.10  # ignore tiny axis components to reduce flicker at low speeds
    max_segment_points: int = 256  # cap how many raw points are stored per segment
