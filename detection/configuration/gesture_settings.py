from dataclasses import dataclass


@dataclass
class GestureSettings:
    start_frames: int = 5
    min_sample: int = 3
    extrema_thresh_fraction: float = 0.65
    extrema_window: int = 3
    invert_x: bool = False
    invert_y: bool = False
