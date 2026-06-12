from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from gamevolt.events.event import Event
from spells.matching.dollar_one.template_library import templates_dir
from spells.scoring.cast_attempt import CastAttempt
from spells.spell_type import SpellType
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.qt.live_trail_widget import LiveTrailWidget
from visualisation.qt.quality_colours import colour_for_score
from visualisation.qt.snapshot_widget import SnapshotWidget
from visualisation.qt.spell_svg_renderer import render_spell_library
from visualisation.qt.spell_targets_widget import SpellTargetsWidget

# Render size for SVG target art; SpellTargetsWidget scales down per tile.
# Generous so retina / large windows still scale *down* (stays crisp) not up.
_SPELL_IMAGE_SIZE = 512
from visualisation.visualiser_protocol import WandVisualiserProtocol
from wand.wand_rotation import WandRotation
from zones.zone import Zone


def _key_token(event: QKeyEvent) -> str:
    """Normalise a key event to a token: digits/letters as text, arrows as 'Up'/'Down'."""
    if event.key() == Qt.Key.Key_Up:
        return "Up"
    if event.key() == Qt.Key.Key_Down:
        return "Down"
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


class QtWandVisualiser(WandVisualiserProtocol):
    """Single dev window: spell targets (left) | live trail (middle) | last-attempt snapshot (right).

    Implements both `WandVisualiserProtocol` (wand trail + cast attempts, fed by RecognitionApp)
    and the zone-visualiser surface (`show_zone`, fed by ZonePresentationController). Zone-select
    key input is surfaced via `key_pressed` for an external controller. Driven cooperatively —
    `update()` pumps the Qt event loop via processEvents(), sharing the app's polled loop.
    """

    def __init__(
        self,
        logger: Logger,
        settings: WandVisualiserSettings,
    ) -> None:
        self._logger = logger
        self._settings = settings
        self._wand_id = settings.wand_id.upper()
        self._quit: Event[Callable[[], None]] = Event()
        self.key_pressed: Event[Callable[[str], None]] = Event()
        self.zone_selected: Event[Callable[[str | None], None]] = Event()
        self._key_callbacks: dict[str, Callable[[], None]] = {}
        self._zone_index: dict[str | None, int] = {}

        self._app = QApplication.instance() or QApplication([])

        # Spell target images are rendered from the layered SVG templates.
        pixmaps = render_spell_library(templates_dir(), _SPELL_IMAGE_SIZE, bg_colour="#ffffff")

        self._targets = SpellTargetsWidget(pixmaps, settings.window.panel_colour, settings.window.text_colour)
        self._live = LiveTrailWidget(settings.trail, settings.window.background_colour)
        self._snapshot = SnapshotWidget(settings)

        self._zone_combo = QComboBox()
        self._zone_combo.activated.connect(self._on_zone_combo_activated)

        panes = QWidget()
        pane_layout = QHBoxLayout(panes)
        pane_layout.setContentsMargins(0, 0, 0, 0)
        pane_layout.setSpacing(2)
        pane_layout.addWidget(self._targets, stretch=1)
        pane_layout.addWidget(self._live, stretch=1)
        pane_layout.addWidget(self._snapshot, stretch=1)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 0)
        layout.setSpacing(4)
        layout.addWidget(self._zone_combo)
        layout.addWidget(panes, stretch=1)

        self._window = _MainWindow(self._on_window_closed, self._on_key)
        self._window.setWindowTitle(settings.window.title)
        self._window.resize(settings.window.width, settings.window.height)
        self._window.setCentralWidget(central)

        palette = self._window.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(settings.window.background_colour))
        self._window.setPalette(palette)

        self._is_running = False

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    # ── WandVisualiserProtocol ──────────────────────────────────
    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self.register_key_callback("c", self.clear)
        self.register_key_callback("q", self._on_window_closed)
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
        self._live.reset()

    def register_key_callback(self, key: str, callback: Callable[[], None]) -> None:
        self._key_callbacks[key] = callback

    def unregister_key_callbacks(self, key: str) -> None:
        self._key_callbacks.pop(key, None)

    def add_rotation(self, wand_position: WandRotation) -> None:
        if wand_position.id.upper() != self._wand_id:
            return
        self._live.add_delta(wand_position.x_delta, wand_position.y_delta)

    def reset_trail(self, wand_id: str) -> None:
        if wand_id.upper() != self._wand_id:
            return
        self._live.reset()

    def show_cast_attempt(self, attempt: CastAttempt) -> None:
        if attempt.wand_id.upper() != self._wand_id:
            return

        # Flash the matched spell tile on every attempt (red when rejected).
        spell = self._spell_for_label(attempt.score.label)
        if spell is not None:
            self._targets.flash(spell, colour_for_score(attempt.score))

        # Snapshot only swaps for attempts clearing the noise gate.
        if self._passes_threshold(attempt):
            self._snapshot.set_attempt(attempt)
        else:
            self._logger.debug(
                f"Snapshot ignoring low attempt '{attempt.score.label}' "
                f"(match {attempt.score.match_accuracy * 100:.0f}% < threshold)."
            )

    # ── zone selection dropdown ─────────────────────────────────
    def set_zone_options(self, options: list[tuple[str | None, str]]) -> None:
        """Populate the zone dropdown. Each option is (zone_id | None, label)."""
        self._zone_combo.blockSignals(True)
        self._zone_combo.clear()
        self._zone_index.clear()
        for i, (zone_id, label) in enumerate(options):
            self._zone_combo.addItem(label, zone_id)
            self._zone_index[zone_id] = i
        self._zone_combo.blockSignals(False)

    def _on_zone_combo_activated(self, index: int) -> None:
        self.zone_selected.invoke(self._zone_combo.itemData(index))

    # ── zone-visualiser surface (fed by ZonePresentationController) ─
    def show_zone(self, zone: Zone | None) -> None:
        zone_id = zone.id if zone is not None else None
        self._targets.set_spells(zone.spell_types if zone is not None else [])
        self._snapshot.clear()  # previous cast result is stale once the zone changes
        index = self._zone_index.get(zone_id)
        if index is not None and index != self._zone_combo.currentIndex():
            self._zone_combo.setCurrentIndex(index)  # programmatic: does not fire `activated`

    def show_spell_instruction(self, spell_type: SpellType) -> None:  # unused; flashing is internal now
        pass

    def show_spell_cast(self, spell_type: SpellType) -> None:
        pass

    def show_spell_cast_coloured(self, spell_type: SpellType, colour: str) -> None:
        pass

    # ── internals ───────────────────────────────────────────────
    def _passes_threshold(self, attempt: CastAttempt) -> bool:
        score = attempt.score
        return score.passed_gates or score.match_accuracy >= self._settings.snapshot.min_match_accuracy

    @staticmethod
    def _spell_for_label(label: str) -> SpellType | None:
        try:
            return SpellType[label]
        except KeyError:
            return None

    def _on_key(self, token: str) -> None:
        self.key_pressed.invoke(token)
        callback = self._key_callbacks.get(token)
        if callback is not None:
            callback()

    def _on_window_closed(self) -> None:
        if not self._is_running:
            return
        self._is_running = False
        self._quit.invoke()
