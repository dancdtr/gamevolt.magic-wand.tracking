from __future__ import annotations

from dataclasses import dataclass

from wands_app.recognition_app import RecognitionApp
from wands_app.tracking_app import TrackingApp


@dataclass
class WandsSystem:
    tracking: TrackingApp
    recognition: RecognitionApp
