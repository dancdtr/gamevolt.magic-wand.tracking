from __future__ import annotations

from pathlib import Path

from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.qt.snapshot_widget import SnapshotWidget
from spells.scoring.cast_attempt import CastAttempt


class QtCastImageRenderer:
    """Renders a cast snapshot (stroke overlay + scoring breakdown) to a PNG by reusing
    the visualiser's `SnapshotWidget`. Requires a live QApplication (owned by the Qt
    visualiser) and must be called on the GUI thread — i.e. from the polled app loop.

    Implements `recording.cast_image_renderer.CastImageRenderer`.
    """

    def __init__(self, settings: WandVisualiserSettings, width: int, height: int) -> None:
        self._widget = SnapshotWidget(settings)
        self._widget.resize(width, height)

    def render(self, attempt: CastAttempt, path: Path) -> None:
        self._widget.set_attempt(attempt)
        # grab() paints the (offscreen, unshown) widget synchronously into a pixmap.
        self._widget.grab().save(str(path), "PNG")
