from __future__ import annotations

from dataclasses import dataclass

from recognition_app import RecognitionApp
from tracking_app import TrackingApp


@dataclass
class WandsSystem:
    tracking: TrackingApp
    recognition: RecognitionApp
