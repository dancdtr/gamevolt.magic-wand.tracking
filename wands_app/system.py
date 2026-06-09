from __future__ import annotations

from dataclasses import dataclass

from cdtr_rtls.cdtr_rtls_integration import CdtrRtlsIntegration
from wands_app.recognition_app import RecognitionApp
from wands_app.tracking_app import TrackingApp


@dataclass
class WandsSystem:
    tracking: TrackingApp
    recognition: RecognitionApp
    cdtr_rtls: CdtrRtlsIntegration | None = None
