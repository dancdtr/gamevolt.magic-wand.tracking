from dataclasses import dataclass


@dataclass
class GestureDetectorSettings:
    start_thresh: float = 1.0
    end_thresh: float = 0.7
    start_frames: int = 5
    end_frames: int = 5
    max_samples: int = 100
