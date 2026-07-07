from gamevolt.configuration.appsetting import appsetting


@appsetting
class WandImuStallDetectorSettings:
    enabled: bool = True
    # No PR for this long counts as a stall candidate. PR arrives ~10Hz when
    # healthy, so anything past a few seconds is already abnormal; kept coarse
    # to ride out momentary radio dropouts.
    stall_after_s: float = 10.0
    # Staleness sweep cadence for the check task.
    check_interval_s: float = 2.0
    # A battery reading older than this no longer proves the tag is alive —
    # without proof-of-life a silent tag is indistinguishable from a wand that
    # is off/out of range. Keep > 2x the battery monitor's poll_interval_s.
    liveness_max_age_s: float = 150.0
