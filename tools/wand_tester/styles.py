"""QSS stylesheet helpers for the wand GUI tester.

Neutral slate surfaces so colour does the talking: each section's groupbox
title is a coloured "chip" (teal / amber / rose / violet) to break up the
space, the LED colour grid keeps its vivid swatches, and violet stays the
single "selected" accent for radio buttons. `app_stylesheet()` is the global
skin; the per-widget helpers below skin the buttons; `group_title_style()`
tints an individual groupbox by section.
"""

from __future__ import annotations

# Base palette — deliberately desaturated so the section accents stand out.
SURFACE = "#161820"  # window background
PANEL = "#1f222c"  # group/tab pane background
PANEL_HI = "#2a2e3a"  # raised control background
BORDER = "#393f4d"
BORDER_HOVER = "#586074"
TEXT = "#e6e9f2"
TEXT_MUTED = "#99a1b3"

# Accents. VIOLET = primary "selected" state; the others colour-code sections.
VIOLET = "#8b7bff"
VIOLET_HI = "#a99bff"
VIOLET_DEEP = "#42386f"
TEAL = "#37b9a0"
AMBER = "#e0a13a"
ROSE = "#e3688a"
GOLD = "#ffb020"  # LED colour-grid selected ring


def app_stylesheet() -> str:
    """Global skin applied once to the QApplication."""
    return f"""
        QWidget {{
            background-color: {SURFACE};
            color: {TEXT};
            font-size: 12px;
        }}
        QLabel {{
            color: {TEXT_MUTED};
            background: transparent;
        }}
        QGroupBox {{
            background-color: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 8px;
            margin-top: 11px;
            padding: 9px 8px 7px 8px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 1px 8px;
            color: {TEXT};
            background-color: {PANEL_HI};
            border: 1px solid {BORDER};
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 11px;
        }}
        QTabWidget::pane {{
            background-color: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 8px;
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: {PANEL_HI};
            color: {TEXT_MUTED};
            border: 1px solid {BORDER};
            border-bottom: none;
            border-top-left-radius: 7px;
            border-top-right-radius: 7px;
            padding: 7px 20px;
            margin-right: 3px;
            font-size: 13px;
            font-weight: bold;
        }}
        QTabBar::tab:selected {{
            background-color: {VIOLET_DEEP};
            color: {TEXT};
            border-color: {VIOLET};
        }}
        QTabBar::tab:hover:!selected {{
            color: {TEXT};
            border-color: {BORDER_HOVER};
        }}
        QComboBox, QSpinBox, QDoubleSpinBox {{
            background-color: {PANEL_HI};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 5px;
            padding: 3px 6px;
            min-height: 20px;
        }}
        QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: {BORDER_HOVER};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {PANEL_HI};
            color: {TEXT};
            border: 1px solid {BORDER};
            selection-background-color: {VIOLET_DEEP};
        }}
        QSlider::groove:horizontal {{
            height: 5px;
            background: {PANEL_HI};
            border: 1px solid {BORDER};
            border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{
            background: {TEAL};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {TEAL};
            border: 2px solid {SURFACE};
            width: 14px;
            margin: -6px 0;
            border-radius: 7px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {GOLD};
        }}
        QToolTip {{
            background-color: {PANEL_HI};
            color: {TEXT};
            border: 1px solid {VIOLET};
            border-radius: 4px;
            padding: 3px 5px;
        }}
    """


def group_title_style(object_name: str, accent: str) -> str:
    """Tint a single groupbox's border + title chip with `accent`. Scoped by
    object name so child widgets are untouched. Set the same name on the box."""
    return f"""
        QGroupBox#{object_name} {{
            border-color: {accent};
        }}
        QGroupBox#{object_name}::title {{
            color: {SURFACE};
            background-color: {accent};
            border-color: {accent};
        }}
    """


def colour_button_style(bg: str, fg: str) -> str:
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: 2px solid {BORDER};
            border-radius: 6px;
            min-width: 70px;
            min-height: 34px;
            font-weight: bold;
        }}
        QPushButton:checked {{
            border: 4px solid {GOLD};
        }}
        QPushButton:hover {{
            border-color: {BORDER_HOVER};
        }}
        QPushButton:checked:hover {{
            border-color: {GOLD};
        }}
    """


def command_button_style() -> str:
    """Checkable radio-style command buttons. Neutral slate until selected,
    then violet — the one consistent 'this is active' cue across sections."""
    return f"""
        QPushButton {{
            background-color: {PANEL_HI};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 6px;
            min-width: 74px;
            min-height: 30px;
            padding: 3px 9px;
            font-weight: bold;
        }}
        QPushButton:checked {{
            background-color: {VIOLET_DEEP};
            border: 2px solid {VIOLET_HI};
            color: #ffffff;
        }}
        QPushButton:hover {{
            border-color: {BORDER_HOVER};
        }}
        QPushButton:checked:hover {{
            border-color: {VIOLET_HI};
        }}
    """


def action_button_style(accent: str) -> str:
    return f"""
        QPushButton {{
            background-color: {accent};
            color: #ffffff;
            border: none;
            border-radius: 6px;
            min-width: 82px;
            min-height: 34px;
            font-weight: bold;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: #ffffff28;
        }}
        QPushButton:pressed {{
            background-color: #00000048;
        }}
    """


def preset_button_style() -> str:
    """Non-checkable quick-fill buttons (haptic effects). Teal hover so they
    read as 'fills the form' actions, distinct from the violet radio state."""
    return f"""
        QPushButton {{
            background-color: {PANEL_HI};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 6px;
            min-width: 74px;
            min-height: 30px;
            padding: 2px 6px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #15463e;
            border-color: {TEAL};
        }}
        QPushButton:pressed {{
            background-color: {TEAL};
            color: {SURFACE};
        }}
    """
