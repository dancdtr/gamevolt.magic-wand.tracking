from typing import List, Tuple

import numpy as np
from scipy.interpolate import interp1d


def low_pass(data: np.ndarray, alpha: float = 0.1) -> np.ndarray:
    """Simple exponential moving average filter."""
    filtered = np.zeros_like(data)
    filtered[0] = data[0]
    for i in range(1, len(data)):
        filtered[i] = alpha * data[i] + (1 - alpha) * filtered[i - 1]
    return filtered


def compute_velocity(accel: np.ndarray, timestamps: np.ndarray) -> np.ndarray:
    """Integrate accelerometer data to velocity (vx, vy)."""
    dt = np.diff(timestamps, prepend=timestamps[0])
    vx = np.cumsum(accel[:, 0] * dt)
    vy = np.cumsum(accel[:, 1] * dt)
    return np.vstack((vx, vy)).T  # shape (N, 2)


def segment_motion(velocities: np.ndarray, v_thresh: float = 0.1) -> List[Tuple[int, int]]:
    """Segment indices based on speed threshold."""
    speed = np.linalg.norm(velocities, axis=1)
    segments: List[Tuple[int, int]] = []
    in_motion = False
    start_idx = 0

    for i, s in enumerate(speed):
        if s > v_thresh and not in_motion:
            in_motion = True
            start_idx = i
        elif (s <= v_thresh or i == len(speed) - 1) and in_motion:
            end_idx = i
            segments.append((start_idx, end_idx))
            in_motion = False

    return segments


def resample_path(path: np.ndarray, N: int = 32) -> np.ndarray:
    """Resample a 2D path to N points by arc-length."""
    diffs = np.diff(path, axis=0)
    seg_lengths = np.linalg.norm(diffs, axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(seg_lengths)))
    f_x = interp1d(cumulative, path[:, 0], kind="linear", assume_sorted=True)
    f_y = interp1d(cumulative, path[:, 1], kind="linear", assume_sorted=True)
    total_len = cumulative[-1]
    new_s = np.linspace(0.0, total_len, N)
    resampled = np.vstack((f_x(new_s), f_y(new_s))).T
    return resampled


def classify_segment(path: np.ndarray) -> str:
    """
    Classify a resampled 2D path into a primitive gesture.
    Returns one of:
      - cardinal/intercardinal directions
      - 'circle', 'semi-circle', 'quarter-circle', 'sine-wave', or 'unknown'
    """
    diffs = np.diff(path, axis=0)
    headings = np.arctan2(diffs[:, 1], diffs[:, 0])
    # Unwrap heading changes
    dtheta = np.diff(headings)
    dtheta_unwrapped = np.unwrap(dtheta)
    total_turn = float(np.sum(dtheta_unwrapped))

    # Curvature estimate
    ds = np.linalg.norm(diffs, axis=1)
    curvature = np.abs(np.diff(headings)) / (ds[:-1] + 1e-6)

    # Line vs arc vs sine
    if abs(total_turn) < np.pi / 4 and np.max(curvature) < 0.1:
        # Straight line; pick nearest cardinal/intercardinal
        avg_heading = float(np.mean(headings))
        angles = np.deg2rad([0, 45, 90, 135, 180, -135, -90, -45])
        labels = ["right", "up-right", "up", "up-left", "left", "down-left", "down", "down-right"]
        diffs_to_angles = [abs(np.unwrap(avg_heading - ang)) for ang in angles]
        idx = int(np.argmin(diffs_to_angles))
        return labels[idx]
    elif abs(total_turn) > 1.7 * np.pi:
        return "circle"
    elif abs(total_turn) > 0.8 * np.pi:
        return "semi-circle"
    elif abs(total_turn) > 0.4 * np.pi:
        return "quarter-circle"
    elif int(np.sum(np.diff(np.sign(curvature)))) >= 2:
        return "sine-wave"
    else:
        return "unknown"


def recognize_primitives(sensor_accels: np.ndarray, timestamps: np.ndarray) -> List[Tuple[int, int, str]]:
    """
    Full pipeline to recognize primitives from raw accelerometer data.

    Args:
      sensor_accels: (N, 3) array of (ax, ay, az)
      timestamps: (N,) array of timestamps in seconds

    Returns:
      List of tuples (start_idx, end_idx, primitive_label)
    """
    # 1. Remove gravity (assuming z-axis aligned)
    linear_accel = sensor_accels.copy()
    linear_accel[:, 2] -= 9.81

    # 2. Low-pass filter X/Y
    linear_accel[:, :2] = low_pass(linear_accel[:, :2])

    # 3. Compute 2D velocities
    velocities = compute_velocity(linear_accel, timestamps)

    # 4. Segment motion
    segments = segment_motion(velocities)

    # 5. Classify each segment
    results: List[Tuple[int, int, str]] = []
    for start, end in segments:
        # Build path by integrating velocity (dx, dy)
        path = np.cumsum(velocities[start:end], axis=0)
        resampled = resample_path(path)
        primitive = classify_segment(resampled)
        results.append((start, end, primitive))

    return results
