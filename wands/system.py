from __future__ import annotations

from dataclasses import dataclass

from wands.recognition_app import RecognitionApp
from wands.tracking_app import TrackingApp


@dataclass
class WandsSystem:
    tracking: TrackingApp
    recognition: RecognitionApp
