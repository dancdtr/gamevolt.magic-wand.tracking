from gamevolt.configuration.appsetting import appsetting


@appsetting
class MotionPhaseTrackerSettings:
    speed_start: float
    speed_stop: float

    # dwell to enter MOVING once above speed_start
    min_state_duration: float

    # still-episode thresholds (total time since still began)
    min_paused_duration: float
    min_holding_duration: float
    min_stopped_duration: float
