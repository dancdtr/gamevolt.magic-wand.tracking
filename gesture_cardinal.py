# gesture_cardinal.py

from typing import List, Tuple

import numpy as np


def compute_velocity(accels: np.ndarray, timestamps: np.ndarray) -> np.ndarray:
    """
    Integrate 2D accelerometer data to velocities (vx, vy).
    accels: (N,3) array of [ax, ay, az]
    timestamps: (N,) array of times in seconds
    Returns: (N,2) array of [vx, vy]
    """
    # time deltas
    dt = np.diff(timestamps, prepend=timestamps[0])
    # integrate X/Y accel
    vx = np.cumsum(accels[:, 0] * dt)
    vy = np.cumsum(accels[:, 1] * dt)
    return np.vstack((vx, vy)).T  # shape (N,2)


def segment_motion(velocities: np.ndarray, v_thresh: float = 0.1) -> List[Tuple[int, int]]:
    """
    Split indices into motion segments when speed > v_thresh.
    velocities: (N,2) array of [vx, vy]
    Returns: list of (start_index, end_index)
    """
    speed = np.linalg.norm(velocities, axis=1)
    segments: List[Tuple[int, int]] = []
    in_motion = False
    start = 0

    for i, s in enumerate(speed):
        if s > v_thresh and not in_motion:
            in_motion = True
            start = i
        elif (s <= v_thresh or i == len(speed) - 1) and in_motion:
            segments.append((start, i))
            in_motion = False

    return segments


def recognize_cardinal(accels: np.ndarray, timestamps: np.ndarray) -> List[Tuple[int, int, str]]:
    """
    Detects simple up/down/left/right segments.
    accels: (N,3) array of raw accel (ax, ay, az)
    timestamps: (N,) array of times in seconds
    Returns: list of (start, end, direction)
    """
    # 1. Compute velocities
    velocities = compute_velocity(accels, timestamps)

    # 2. Segment into motion bursts
    segments = segment_motion(velocities)

    results: List[Tuple[int, int, str]] = []
    for start, end in segments:
        # average velocity in segment
        vx_mean = float(np.mean(velocities[start:end, 0]))
        vy_mean = float(np.mean(velocities[start:end, 1]))

        # classify by dominant axis
        if abs(vx_mean) > abs(vy_mean):
            direction = "right" if vx_mean > 0 else "left"
        else:
            direction = "up" if vy_mean > 0 else "down"

        results.append((start, end, direction))

    return results


# Example usage
if __name__ == "__main__":
    # simulate or load your SensorData list here...
    # accels = np.array([[d.accel.x, d.accel.y, d.accel.z] for d in sensor_data])
    # times  = np.array([d.timestamp_ms/1000 for d in sensor_data])
    # primitives = recognize_cardinal(accels, times)
    # print(primitives)
    pass
