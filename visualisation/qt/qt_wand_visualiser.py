from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gamevolt.events.event import Event
from spells.matching.dollar_one.template_library import templates_dir
from spells.scoring.cast_attempt import CastAttempt
from spells.scoring.scoring_modifier import ScoringModifier
from spells.settings.spell_scoring_settings import SpellScoringSettings
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_difficulty import difficulty_for_template
from spells.spell_info import load_spell_info
from spells.spell_type import SpellType
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.qt.auto_advance_settings import AutoAdvanceSettings
from visualisation.qt.live_trail_widget import LiveTrailWidget
from visualisation.qt.quality_colours import NOISE_COLOUR, colour_for_score
from visualisation.qt.settings_panel import SettingsPanel
from visualisation.qt.snapshot_widget import SnapshotWidget
from visualisation.qt.spell_info_card import SpellInfoCard
from visualisation.qt.spell_svg_renderer import render_spell_library
from visualisation.qt.spell_targets_widget import SpellTargetsWidget


def _build_difficulties(
    logger: Logger, scoring: SpellScoringSettings
) -> dict[SpellType, float]:
    """Precompute the 1–10 cast-difficulty rating per spell from its template +
    resolved scoring thresholds. Product-only and fail-soft (unsampleable templates
    fall back to a threshold-only rating); a missing template is simply omitted."""
    out: dict[SpellType, float] = {}
    directory = templates_dir()
    logger.info("generating spell difficulty ratings from templates...")
    for spell in SpellType:
        if spell is SpellType.NONE:
            continue
        svg = directory / f"spell_template_{spell.name.lower()}.svg"
        if not svg.exists():
            continue
        settings = scoring.spell_settings(spell.name)
        thresholds = settings.quality_thresholds
        mastered = thresholds.get(SpellCastQuality.MASTERED) or (max(thresholds.values()) if thresholds else 90)
        out[spell] = difficulty_for_template(
            svg,
            min_match_accuracy=settings.gates.min_match_accuracy,
            mastered_threshold=float(mastered),
            logger=logger,
        )
    return out

# Render size for SVG target art; SpellTargetsWidget scales down per tile.
# Generous so retina / large windows still scale *down* (stays crisp) not up.
_SPELL_IMAGE_SIZE = 512

# Record button: green when armed, grey when no name yet, pulsing red while recording.
_RECORD_IDLE_STYLE = (
    "QPushButton { background:#16a34a; color:#ffffff; font-weight:bold;"
    " border:none; border-radius:6px; padding:6px 16px; }"
    "QPushButton:hover:enabled { background:#22c55e; }"
    "QPushButton:disabled { background:#2b2b2b; color:#666666; }"
)
_RECORD_ACTIVE_STYLE = (
    "QPushButton {{ background:{bg}; color:#ffffff; font-weight:bold;"
    " border:none; border-radius:6px; padding:6px 16px; }}"
)
from visualisation.visualiser_protocol import WandVisualiserProtocol
from wand.wand_rotation import WandRotation
from zones.zone import Zone


def _key_token(event: QKeyEvent) -> str:
    """Normalise a key event to a token: digits/letters as text, arrows as 'Up'/'Down'."""
    if event.key() == Qt.Key.Key_Up:
        return "Up"
    if event.key() == Qt.Key.Key_Down:
        return "Down"
    if event.key() == Qt.Key.Key_Escape:
        return "Escape"
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        return "Return"
    return event.text()


class _NameField(QLineEdit):
    """Name entry that lets the zone-cycle keys (Up/Down), Escape and Return bubble
    to the window instead of being consumed by the line edit (Return is the
    raw-line-dump shortcut)."""

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt override)
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()
            return
        super().keyPressEvent(event)


class _MainWindow(QMainWindow):
    def __init__(
        self,
        on_close: Callable[[], None],
        on_key: Callable[[str], None],
        on_resize: Callable[[], None],
    ) -> None:
        super().__init__()
        self._on_close = on_close
        self._on_key = on_key
        self._on_resize = on_resize

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt override)
        self._on_close()
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        self._on_resize()

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
        spell_scoring: SpellScoringSettings,
    ) -> None:
        self._logger = logger
        self._settings = settings
        self._wand_id = settings.wand_id.upper()
        self._quit: Event[Callable[[], None]] = Event()
        self._reset_xp_requested: Event[Callable[[], None]] = Event()
        # Fires when the diagnostic re-enable-IMU button is clicked; the builder
        # routes it to the single-anchor client's CMD0 send.
        self._enable_imu_requested: Event[Callable[[], None]] = Event()
        self._record_session_changed: Event[Callable[[bool, str], None]] = Event()
        # Fires on a recognized cast (rudimentary+), carrying the awarded quality tier;
        # QtZoneControls uses it (and the tier) to decide whether to auto-advance.
        self._cast_recognized: Event[Callable[[SpellCastQuality], None]] = Event()
        # Fires when a scoring-modifier toggle flips; system_builder routes it to the scorer.
        self._scoring_modifier_changed: Event[Callable[[ScoringModifier, bool], None]] = Event()
        # Fires when the in-park-only toggle flips; QtZoneControls refilters the dropdown.
        self._in_park_only_changed: Event[Callable[[bool], None]] = Event()
        self._auto_advance = AutoAdvanceSettings()
        self.key_pressed: Event[Callable[[str], None]] = Event()
        self.zone_selected: Event[Callable[[str | None], None]] = Event()
        self._key_callbacks: dict[str, Callable[[], None]] = {}
        self._zone_index: dict[str | None, int] = {}
        self._pending_battery: tuple[int, float] | None = None

        self._app = QApplication.instance() or QApplication([])

        # Spell target tiles: black ink on white, tiled for the multi-spell zone view.
        pixmaps = render_spell_library(templates_dir(), _SPELL_IMAGE_SIZE, bg_colour="#ffffff")
        # Card art: black ink on transparent — the card draws its own parchment inset behind it.
        card_pixmaps = render_spell_library(templates_dir(), _SPELL_IMAGE_SIZE)

        spell_info = load_spell_info(logger)
        difficulties = _build_difficulties(logger, spell_scoring)

        self._targets = SpellTargetsWidget(pixmaps, settings.window.panel_colour, settings.window.text_colour)
        self._info_card = SpellInfoCard(
            spell_info, difficulties, card_pixmaps, settings.window.panel_colour, settings.window.text_colour
        )
        # Left pane swaps between the info card (single-spell zone) and target tiles (multi-spell).
        self._left = QStackedWidget()
        self._left.addWidget(self._targets)
        self._left.addWidget(self._info_card)

        self._live = LiveTrailWidget(settings.trail, settings.window.background_colour)
        self._snapshot = SnapshotWidget(settings)

        self._zone_combo = QComboBox()
        self._zone_combo.activated.connect(self._on_zone_combo_activated)

        toolbar = self._build_toolbar()

        panes = QWidget()
        pane_layout = QHBoxLayout(panes)
        pane_layout.setContentsMargins(0, 0, 0, 0)
        pane_layout.setSpacing(2)
        pane_layout.addWidget(self._left, stretch=1)
        pane_layout.addWidget(self._live, stretch=1)
        pane_layout.addWidget(self._snapshot, stretch=1)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 0)
        layout.setSpacing(4)
        layout.addWidget(toolbar)
        layout.addWidget(panes, stretch=1)

        self._window = _MainWindow(self._on_window_closed, self._on_key, self._reposition_settings)
        self._window.setWindowTitle(settings.window.title)
        self._window.resize(settings.window.width, settings.window.height)
        self._window.setCentralWidget(central)

        # Battery readout, fed by the single-anchor battery monitor via
        # `set_wand_battery`. Lives bottom-right in the status bar so passive
        # telemetry stays out of the control toolbar. Placeholder until the
        # first GDHR response lands.
        self._battery_label = QLabel("—")
        self._battery_label.setToolTip("Wand battery (GDHR poll)")
        self._battery_label.setStyleSheet("color:#dddddd; font-size:13px; padding:0px 6px;")
        self._window.statusBar().addPermanentWidget(self._battery_label)
        self._window.statusBar().setSizeGripEnabled(False)

        palette = self._window.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(settings.window.background_colour))
        self._window.setPalette(palette)

        # Slide-in settings overlay: parented to `central`, positioned manually over the panes.
        self._settings_panel = SettingsPanel(
            central,
            self._auto_advance,
            settings.window.panel_colour,
            settings.window.text_colour,
            on_trail_toggled=self._on_trail_toggled,
            on_scoring_modifier=self._scoring_modifier_changed.invoke,
            on_in_park_toggled=self._in_park_only_changed.invoke,
            close_trigger=self._settings_button,
        )

        self._is_running = False

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    @property
    def reset_xp_requested(self) -> Event[Callable[[], None]]:
        return self._reset_xp_requested

    @property
    def enable_imu_requested(self) -> Event[Callable[[], None]]:
        return self._enable_imu_requested

    @property
    def record_session_changed(self) -> Event[Callable[[bool, str], None]]:
        return self._record_session_changed

    # ── top toolbar ─────────────────────────────────────────────
    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self._settings_button = QPushButton("⚙")
        self._settings_button.setToolTip("Settings")
        # Big gear glyph; height is pinned to the record button below so it doesn't grow.
        self._settings_button.setStyleSheet(
            "QPushButton { padding:0px 12px; border:none; border-radius:6px;"
            " background:#2b2b2b; color:#dddddd; font-size:20px; }"
            "QPushButton:hover { background:#3a3a3a; }"
        )
        self._settings_button.clicked.connect(self._on_settings_clicked)

        # Reset-XP shortcut, mirroring the settings-panel button. Hidden while the XP
        # scoring modifier is disabled (no XP state to reset then).
        self._reset_xp_button = QPushButton("Reset XP")
        self._reset_xp_button.setToolTip("Reset accumulated XP")
        self._reset_xp_button.setStyleSheet(
            "QPushButton { padding:0px 12px; border:none; border-radius:6px;"
            " background:#2b2b2b; color:#dddddd; font-size:13px; }"
            "QPushButton:hover { background:#3a3a3a; }"
        )
        self._reset_xp_button.clicked.connect(self._reset_xp_requested.invoke)
        # Track XP-modifier flips so we can show/hide the button live.
        self._scoring_modifier_changed.subscribe(self._on_scoring_modifier_for_toolbar)

        # Diagnostic: manually re-send the CMD0 IMU-enable — for testing whether
        # a silently stalled PR stream resumes without a power cycle.
        self._enable_imu_button = QPushButton("IMU ⟳")
        self._enable_imu_button.setToolTip("Restart IMU stream on tracked wands (GETD type + CMD0 off/on)")
        self._enable_imu_button.setStyleSheet(
            "QPushButton { padding:0px 12px; border:none; border-radius:6px;"
            " background:#2b2b2b; color:#dddddd; font-size:13px; }"
            "QPushButton:hover { background:#3a3a3a; }"
        )
        self._enable_imu_button.clicked.connect(self._enable_imu_requested.invoke)

        self._name_field = _NameField()
        self._name_field.textChanged.connect(self._on_name_changed)

        self._record_toggle = QPushButton("⏺  Record")
        self._record_toggle.setCheckable(True)
        self._record_toggle.setEnabled(False)  # needs a name first
        self._record_toggle.setStyleSheet(_RECORD_IDLE_STYLE)
        # Fix the width so the button doesn't jump size between Record / Stop states.
        self._record_toggle.setFixedWidth(self._record_toggle.fontMetrics().horizontalAdvance("⏹  Stop — REC") + 48)
        self._record_toggle.toggled.connect(self._on_record_toggled)

        # Pin the gear + reset + IMU buttons to the record button's height so they align.
        self._record_toggle.ensurePolished()
        self._settings_button.setFixedHeight(self._record_toggle.sizeHint().height())
        self._reset_xp_button.setFixedHeight(self._record_toggle.sizeHint().height())
        self._enable_imu_button.setFixedHeight(self._record_toggle.sizeHint().height())

        # Pulses the record button between two reds while a session is recording.
        self._record_blink_on = False
        self._record_blink = QTimer()
        self._record_blink.setInterval(600)
        self._record_blink.timeout.connect(self._pulse_record_button)

        # Zone/spell picker sits top-left, bounded so it doesn't stretch across the window.
        self._zone_combo.setMaximumWidth(280)
        row.addWidget(self._zone_combo)
        row.addStretch(1)
        row.addWidget(QLabel("Name:"))
        row.addWidget(self._name_field, stretch=1)
        row.addWidget(self._enable_imu_button)
        row.addWidget(self._reset_xp_button)
        row.addWidget(self._record_toggle)
        row.addWidget(self._settings_button)
        return bar

    def _on_scoring_modifier_for_toolbar(self, modifier: ScoringModifier, enabled: bool) -> None:
        # The toolbar Reset-XP shortcut only makes sense while XP scoring is on.
        if modifier is ScoringModifier.XP:
            self._reset_xp_button.setVisible(enabled)

    def _on_settings_clicked(self) -> None:
        self._reposition_settings()  # ensure geometry is current before sliding in
        self._settings_panel.toggle()

    def _reposition_settings(self) -> None:
        self._settings_panel.reposition()

    @property
    def auto_advance_settings(self) -> AutoAdvanceSettings:
        return self._auto_advance

    @property
    def cast_recognized(self) -> Event[Callable[[SpellCastQuality], None]]:
        return self._cast_recognized

    @property
    def scoring_modifier_changed(self) -> Event[Callable[[ScoringModifier, bool], None]]:
        return self._scoring_modifier_changed

    @property
    def in_park_only_changed(self) -> Event[Callable[[bool], None]]:
        return self._in_park_only_changed

    def _on_trail_toggled(self, checked: bool) -> None:
        self._live.set_enabled(checked)

    def _on_name_changed(self, text: str) -> None:
        # Record can only arm once a name is present; the field locks while recording.
        self._record_toggle.setEnabled(bool(text.strip()))

    def _on_record_toggled(self, checked: bool) -> None:
        name = self._name_field.text().strip()
        self._name_field.setReadOnly(checked)

        if checked:
            self._record_toggle.setText("⏹  Stop — REC")
            self._record_blink_on = True
            self._pulse_record_button()
            self._record_blink.start()
        else:
            self._record_blink.stop()
            self._record_toggle.setText("⏺  Record")
            self._record_toggle.setStyleSheet(_RECORD_IDLE_STYLE)

        self._record_session_changed.invoke(checked, name)
        if not checked:
            # Clear the name on stop so the next session needs a name entered intentionally
            # (this also disables the record button until a fresh name is typed).
            self._name_field.clear()

    def _pulse_record_button(self) -> None:
        self._record_blink_on = not self._record_blink_on
        bg = "#dc2626" if self._record_blink_on else "#7f1d1d"
        self._record_toggle.setStyleSheet(_RECORD_ACTIVE_STYLE.format(bg=bg))

    # ── WandVisualiserProtocol ──────────────────────────────────
    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self.register_key_callback("Escape", self._on_window_closed)
        self._window.show()
        self._reposition_settings()  # park the panel off-screen right once sized

    def stop(self) -> None:
        if not self._is_running:
            return
        self._is_running = False
        self._record_blink.stop()
        self._window.close()
        self._app.processEvents()

    def update(self) -> None:
        if not self._is_running:
            return
        self._apply_pending_battery()
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

    def set_wand_battery(self, wand_id: str, millivolts: int, percent: float) -> None:
        # Called from the serial receive thread — stash only; `update()` applies
        # it on the Qt thread.
        if wand_id.upper() != self._wand_id:
            return
        self._pending_battery = (millivolts, percent)

    def _apply_pending_battery(self) -> None:
        pending = self._pending_battery
        if pending is None:
            return
        self._pending_battery = None
        millivolts, percent = pending
        colour = "#66cc66" if percent > 50 else "#e0b040" if percent > 20 else "#e05050"
        self._battery_label.setText(f"{millivolts / 1000:.2f}V ({percent:.0f}%)")
        self._battery_label.setStyleSheet(f"color:{colour}; font-size:13px;")

    def reset_trail(self, wand_id: str) -> None:
        if wand_id.upper() != self._wand_id:
            return
        self._live.reset()

    def show_cast_attempt(self, attempt: CastAttempt) -> None:
        if attempt.wand_id.upper() != self._wand_id:
            return

        # Flash the matched spell tile on every attempt: quality colour when it clears the
        # noise gate (red if rejected), grey for sub-threshold noise flicks.
        passes = self._passes_threshold(attempt)
        spell = self._spell_for_label(attempt.score.label)
        if spell is not None:
            self._targets.flash(spell, colour_for_score(attempt.score) if passes else NOISE_COLOUR)

        # Snapshot only swaps for attempts clearing the noise gate.
        if passes:
            self._snapshot.set_attempt(attempt)
        else:
            self._logger.debug(
                f"Snapshot ignoring low attempt '{attempt.score.label}' (match {attempt.score.match_accuracy * 100:.0f}% < threshold)."
            )

        # Rudimentary+ cast: signal auto-advance with the awarded tier (QtZoneControls
        # decides whether to act based on the minimum-quality setting).
        if attempt.score.recognized:
            assert attempt.score.quality is not None  # guaranteed when recognized
            self._cast_recognized.invoke(attempt.score.quality)

    # ── zone selection dropdown ─────────────────────────────────
    def set_zone_options(
        self, options: list[tuple[str | None, str]], current: str | None = None
    ) -> None:
        """Populate the zone dropdown. Each option is (zone_id | None, label).

        `current` re-selects that zone after repopulating (used when the option set is
        refiltered live) so the combo keeps showing the active zone.
        """
        self._zone_combo.blockSignals(True)
        self._zone_combo.clear()
        self._zone_index.clear()
        for i, (zone_id, label) in enumerate(options):
            self._zone_combo.addItem(label, zone_id)
            self._zone_index[zone_id] = i
        index = self._zone_index.get(current)
        if index is not None:
            self._zone_combo.setCurrentIndex(index)
        self._zone_combo.blockSignals(False)

    def _on_zone_combo_activated(self, index: int) -> None:
        self.zone_selected.invoke(self._zone_combo.itemData(index))

    # ── zone-visualiser surface (fed by ZonePresentationController) ─
    def show_zone(self, zone: Zone | None) -> None:
        zone_id = zone.id if zone is not None else None
        spells = [s for s in (zone.spell_types if zone is not None else []) if s is not SpellType.NONE]

        # A single-spell zone shows the full Primer card; anything else falls back to
        # the tiled targets view.
        if len(spells) == 1:
            self._info_card.set_spell(spells[0])
            self._left.setCurrentWidget(self._info_card)
        else:
            self._targets.set_spells(spells)
            self._left.setCurrentWidget(self._targets)

        # Normally the previous cast result is stale once the zone changes. But when
        # auto-advancing, the zone change *is* the result of that cast — keep it on
        # screen so you can see how the last spell scored.
        if not self._auto_advance.auto_advance:
            self._snapshot.clear()
        index = self._zone_index.get(zone_id)
        if index is not None and index != self._zone_combo.currentIndex():
            self._zone_combo.setCurrentIndex(index)  # programmatic: does not fire `activated`

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
