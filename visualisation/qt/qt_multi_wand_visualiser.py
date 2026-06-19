from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gamevolt.events.event import Event
from spells.scoring.cast_attempt import CastAttempt
from visualisation.configuration.multi_wand_visualiser_settings import MultiWandVisualiserSettings
from visualisation.qt.multi_wand_trail_widget import MultiWandTrailWidget
from visualisation.qt.quality_colours import colour_for_score
from visualisation.qt.wand_legend_widget import WandLegendWidget
from visualisation.visualiser_protocol import WandVisualiserProtocol
from wand.wand_rotation import WandRotation

_LEGEND_MARGIN = 12


def _key_token(event: QKeyEvent) -> str:
    if event.key() == Qt.Key.Key_Escape:
        return "Escape"
    return event.text()


class _MainWindow(QMainWindow):
    def __init__(self, on_close: Callable[[], None], on_key: Callable[[str], None]) -> None:
        super().__init__()
        self._on_close = on_close
        self._on_key = on_key

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt override)
        self._on_close()
        super().closeEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt override)
        self._on_key(_key_token(event))
        super().keyPressEvent(event)


class QtMultiWandVisualiser(WandVisualiserProtocol):
    """RTLS visualiser: every active wand's live trail overlaid on one canvas, colour-keyed by id,
    with a corner legend of id · zone · spell targets · last cast.

    Implements `WandVisualiserProtocol` (fed by RecognitionApp: rotations, settle resets, cast
    attempts) plus `wand_entered_zone` / `wand_exited_zone` (wired from the zone manager by the
    builder) which add/remove a wand's trail and legend row. Driven cooperatively — `update()`
    pumps the Qt event loop via processEvents(), sharing the app's polled loop."""

    def __init__(
        self,
        logger: Logger,
        settings: MultiWandVisualiserSettings,
        wand_ids: list[str],
    ) -> None:
        self._logger = logger
        self._settings = settings
        self._quit: Event[Callable[[], None]] = Event()
        self._reset_xp_requested: Event[Callable[[], None]] = Event()
        self._record_session_changed: Event[Callable[[bool, str], None]] = Event()
        self._key_callbacks: dict[str, Callable[[], None]] = {}

        # Stable id -> colour assignment, palette wrapped over the tracked wands.
        palette = settings.palette or [settings.trail.line_colour]
        self._colours: dict[str, str] = {
            wand_id.upper(): palette[i % len(palette)] for i, wand_id in enumerate(wand_ids)
        }

        self._app = QApplication.instance() or QApplication([])

        self._canvas = MultiWandTrailWidget(settings.trail, settings.window.background_colour)
        for wand_id, colour in self._colours.items():
            self._canvas.set_colour(wand_id, colour)

        # Legend floats in the top-left corner over the canvas.
        self._legend = WandLegendWidget(settings.window.text_colour)
        self._legend.setParent(self._canvas)
        self._legend.move(_LEGEND_MARGIN, _LEGEND_MARGIN)
        self._legend.show()

        toolbar = self._build_toolbar()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        layout.addWidget(toolbar)
        layout.addWidget(self._canvas, stretch=1)

        self._window = _MainWindow(self._on_window_closed, self._on_key)
        self._window.setWindowTitle(settings.window.title)
        self._window.resize(settings.window.width, settings.window.height)
        self._window.setCentralWidget(central)

        palette_q = self._window.palette()
        palette_q.setColor(QPalette.ColorRole.Window, QColor(settings.window.background_colour))
        self._window.setPalette(palette_q)

        self._is_running = False

    # ── events ──────────────────────────────────────────────────
    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    @property
    def reset_xp_requested(self) -> Event[Callable[[], None]]:
        return self._reset_xp_requested

    @property
    def record_session_changed(self) -> Event[Callable[[bool, str], None]]:
        return self._record_session_changed

    # ── toolbar ─────────────────────────────────────────────────
    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self._reset_xp_button = QPushButton("Reset XP")
        self._reset_xp_button.clicked.connect(self._reset_xp_requested.invoke)

        row.addWidget(self._reset_xp_button)
        row.addStretch(1)
        return bar

    # ── WandVisualiserProtocol ──────────────────────────────────
    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self.register_key_callback("Escape", self._on_window_closed)
        self._window.show()

    def stop(self) -> None:
        if not self._is_running:
            return
        self._is_running = False
        self._window.close()
        self._app.processEvents()

    def update(self) -> None:
        if not self._is_running:
            return
        self._app.processEvents()

    def clear(self) -> None:
        self._canvas.clear_all()

    def register_key_callback(self, key: str, callback: Callable[[], None]) -> None:
        self._key_callbacks[key] = callback

    def unregister_key_callbacks(self, key: str) -> None:
        self._key_callbacks.pop(key, None)

    def add_rotation(self, wand_position: WandRotation) -> None:
        self._canvas.add_delta(wand_position.id.upper(), wand_position.x_delta, wand_position.y_delta)

    def reset_trail(self, wand_id: str) -> None:
        # Per-stroke clear: the wand settled, so wipe its accrued stroke but keep its slot.
        self._canvas.reset(wand_id.upper())

    def show_cast_attempt(self, attempt: CastAttempt) -> None:
        pct = attempt.score.match_accuracy * 100
        text = f"{attempt.score.label} {pct:.0f}%"
        self._legend.set_last_cast(attempt.wand_id.upper(), text, colour_for_score(attempt.score))

    # ── zone hooks (wired from the zone manager by the builder) ──
    def wand_entered_zone(self, wand_id: str, zone_id: str, spell_labels: list[str]) -> None:
        wand_id = wand_id.upper()
        self._canvas.set_colour(wand_id, self._colour_for(wand_id))
        self._legend.upsert(wand_id, self._colour_for(wand_id), zone_id, spell_labels)

    def wand_exited_zone(self, wand_id: str) -> None:
        wand_id = wand_id.upper()
        self._canvas.remove(wand_id)
        self._legend.remove(wand_id)

    # ── internals ───────────────────────────────────────────────
    def _colour_for(self, wand_id: str) -> str:
        return self._colours.get(wand_id, self._settings.trail.line_colour)

    def _on_key(self, token: str) -> None:
        callback = self._key_callbacks.get(token)
        if callback is not None:
            callback()

    def _on_window_closed(self) -> None:
        if not self._is_running:
            return
        self._is_running = False
        self._quit.invoke()
