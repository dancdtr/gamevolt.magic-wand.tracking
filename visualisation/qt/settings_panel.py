from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from spells.scoring.scoring_modifier import ScoringModifier
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_tag import SpellTag
from visualisation.qt.auto_advance_settings import AutoAdvanceSettings

_PANEL_WIDTH = 280
_SLIDE_MS = 180

# Spell-tag filter checkboxes, in display order.
_TAG_LABELS = {
    SpellTag.PARK: "In park",
    SpellTag.PRIMER: "Spells Primer",
    SpellTag.CDTR: "CDTR originals",
}

# Scoring-modifier checkboxes, in display order.
_MODIFIER_LABELS = {
    ScoringModifier.XP: "XP bonus",
    ScoringModifier.CADENCE: "Cadence bonus",
    ScoringModifier.TEMPO: "Tempo bonus",
    ScoringModifier.PITY: "Pity bonus",
}

# Minimum-advance-quality dropdown, weakest → strongest. A ★ per tier hints at the level.
_QUALITY_LABELS = {
    SpellCastQuality.RUDIMENTARY: "★ Rudimentary",
    SpellCastQuality.SKILLED: "★★ Skilled",
    SpellCastQuality.EXPERIENCED: "★★★ Experienced",
    SpellCastQuality.MASTERED: "★★★★ Mastered",
}


class SettingsPanel(QFrame):
    """Dev settings overlay that slides in from the right edge.

    Parented to the window's central widget but kept out of its layout — positioned
    manually and animated on its `pos`. Auto-advance toggles write straight into the
    shared `AutoAdvanceSettings` (zone controls read it live); trail / XP controls
    call back into the visualiser, which owns that state.
    """

    def __init__(
        self,
        parent: QWidget,
        settings: AutoAdvanceSettings,
        panel_colour: str,
        text_colour: str,
        *,
        on_trail_toggled: Callable[[bool], None],
        on_scoring_modifier: Callable[[ScoringModifier, bool], None],
        on_enabled_tags_changed: Callable[[frozenset[SpellTag]], None],
        trail_enabled: bool = True,
        close_trigger: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._on_trail_toggled = on_trail_toggled
        self._on_scoring_modifier = on_scoring_modifier
        self._on_enabled_tags_changed = on_enabled_tags_changed
        # Widget that toggles the panel (the gear button): a press on it is handled by its own
        # toggle, so the click-outside filter must ignore it to avoid closing then reopening.
        self._close_trigger = close_trigger
        self._open = False

        self.setFixedWidth(_PANEL_WIDTH)
        # Opaque styled background so the overlay fully covers the panes behind it.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"SettingsPanel {{ background:{panel_colour}; border-left:1px solid #3a3a3a; }}"
            f" QCheckBox, QLabel {{ color:{text_colour}; }}"
            f" QComboBox {{ color:{text_colour}; background:#2a2a2a; border:1px solid #3a3a3a;"
            " padding:3px 6px; }"
            f" QComboBox:disabled {{ color:#666; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header: title left, close (✕) top-right — sits where the gear button that opened it is.
        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet(f"color:{text_colour}; font-weight:bold; font-size:15px;")
        header.addWidget(title)
        header.addStretch(1)

        close = QPushButton("✕")
        close.setFixedSize(39, 39)
        close.setToolTip("Close")
        close.setStyleSheet(
            f"QPushButton {{ color:{text_colour}; border:none; font-size:22px; }}"
            " QPushButton:hover { color:#ffffff; }"
        )
        close.clicked.connect(self.close_panel)
        header.addWidget(close)
        layout.addLayout(header)

        layout.addWidget(self._section("Display", text_colour))

        self._trail = QCheckBox("Show trail")
        self._trail.setChecked(trail_enabled)
        self._trail.toggled.connect(self._on_trail)
        layout.addWidget(self._trail)

        layout.addWidget(self._section("Spell selection", text_colour))

        # One checkbox per tag; the pool is the union of the checked tags.
        for tag, label in _TAG_LABELS.items():
            box = QCheckBox(label)
            box.setChecked(tag in settings.enabled_tags)
            box.toggled.connect(lambda checked, t=tag: self._on_tag(t, checked))
            layout.addWidget(box)

        self._random = QCheckBox("Randomise next spell")
        self._random.setChecked(settings.randomise)
        self._random.toggled.connect(self._on_random)
        layout.addWidget(self._random)

        self._auto = QCheckBox("Auto-advance after cast")
        self._auto.setChecked(settings.auto_advance)
        self._auto.toggled.connect(self._on_auto)
        layout.addWidget(self._auto)

        self._min_quality_label = QLabel("Advance with")
        layout.addWidget(self._min_quality_label)

        self._min_quality = QComboBox()
        for quality, label in _QUALITY_LABELS.items():
            self._min_quality.addItem(label, quality)
        self._min_quality.setCurrentIndex(self._min_quality.findData(settings.min_advance_quality))
        self._min_quality.currentIndexChanged.connect(self._on_min_quality)
        layout.addWidget(self._min_quality)

        layout.addWidget(self._section("Scoring modifiers", text_colour))

        # All modifiers default on (matching the scorer); flipping one emits (modifier, state).
        for modifier, label in _MODIFIER_LABELS.items():
            box = QCheckBox(label)
            box.setChecked(True)
            box.toggled.connect(lambda checked, m=modifier: self._on_scoring_modifier(m, checked))
            layout.addWidget(box)

        layout.addStretch(1)

        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(_SLIDE_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self._on_anim_finished)

        self._sync_enabled()
        self.hide()

    @staticmethod
    def _section(text: str, text_colour: str) -> QLabel:
        label = QLabel(text.upper())
        label.setStyleSheet(f"color:{text_colour}; font-weight:bold; font-size:11px; margin-top:8px;")
        return label

    # ── toggle handlers ─────────────────────────────────────────
    def _on_auto(self, checked: bool) -> None:
        self._settings.auto_advance = checked
        self._sync_enabled()

    def _on_random(self, checked: bool) -> None:
        self._settings.randomise = checked

    def _on_tag(self, tag: SpellTag, checked: bool) -> None:
        if checked:
            self._settings.enabled_tags.add(tag)
        else:
            self._settings.enabled_tags.discard(tag)
        self._on_enabled_tags_changed(frozenset(self._settings.enabled_tags))

    def _on_min_quality(self, index: int) -> None:
        self._settings.min_advance_quality = self._min_quality.itemData(index)

    def _on_trail(self, checked: bool) -> None:
        self._on_trail_toggled(checked)

    def _sync_enabled(self) -> None:
        # Randomise + min-quality only mean anything while auto-advancing; grey out otherwise.
        auto = self._auto.isChecked()
        self._random.setEnabled(auto)
        self._min_quality.setEnabled(auto)
        self._min_quality_label.setEnabled(auto)

    # ── slide in / out ──────────────────────────────────────────
    def toggle(self) -> None:
        self.close_panel() if self._open else self.open_panel()

    def open_panel(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        self._open = True
        self.setFixedHeight(parent.height())
        self.move(parent.width(), 0)  # start off-screen right
        self.show()
        self.raise_()
        self._animate_to(parent.width() - self.width())
        app = QApplication.instance()
        if app is not None:
            # Drop focus from the name field etc. so its highlight/focus ring doesn't paint
            # over the panel, then watch for clicks outside the panel.
            focused = app.focusWidget()
            if focused is not None:
                focused.clearFocus()
            app.installEventFilter(self)  # watch for clicks outside the panel

    def close_panel(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        self._open = False
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        self._animate_to(parent.width())

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802 (Qt override)
        """Close the panel when a mouse press lands anywhere outside it (except the gear)."""
        if self._open and event.type() == QEvent.Type.MouseButtonPress and isinstance(obj, QWidget):
            outside = obj is not self and not self.isAncestorOf(obj)
            on_trigger = self._close_trigger is not None and (
                obj is self._close_trigger or self._close_trigger.isAncestorOf(obj)
            )
            if outside and not on_trigger:
                self.close_panel()
        return super().eventFilter(obj, event)

    def reposition(self) -> None:
        """Keep the panel pinned to the right edge / full height on window resize."""
        parent = self.parentWidget()
        if parent is None:
            return
        self.setFixedHeight(parent.height())
        x = parent.width() - self.width() if self._open else parent.width()
        self.move(x, 0)

    def _animate_to(self, x: int) -> None:
        self._anim.stop()
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(QPoint(x, 0))
        self._anim.start()

    def _on_anim_finished(self) -> None:
        if not self._open:
            self.hide()
