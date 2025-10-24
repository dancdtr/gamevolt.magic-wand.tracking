from dataclasses import dataclass


@dataclass
class ImuInputSettings:
    port: str | None  # autodetect if None
    baudrate: int
    read_timeout_s: float

    # Output cadence
    emit_hz: float  # downsample to this rate
    max_step: float  # clamp per-emission |delta| (safety)

    # Gyro→delta mapping (deg of wrist movement to 2D delta)
    # delta_x += yaw_deg_delta * sens_yaw_deg_to_unit
    # delta_y += pitch_deg_delta * sens_pitch_deg_to_unit
    sens_yaw_deg_to_unit: float  # eg 0.02 = 50° -> 1.0 unit
    sens_pitch_deg_to_unit: float

    # Jitter control
    deadband_dps: float  # ignore very small gyro rates
    smooth_alpha: float  # simple EMA on gyro rates (0..1)

    # Axis mapping
    invert_x: bool
    invert_y: bool

    # Robustness
    drop_if_large_gap_ms: int  # reset accumulators if stream stutters
