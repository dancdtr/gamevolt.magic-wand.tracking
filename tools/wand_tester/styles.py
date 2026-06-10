"""QSS stylesheet helpers for the wand GUI tester."""

from __future__ import annotations


def colour_button_style(bg: str, fg: str) -> str:
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: 2px solid #555;
            border-radius: 4px;
            min-width: 90px;
            min-height: 44px;
            font-weight: bold;
        }}
        QPushButton:checked {{
            border: 6px solid #ffaa00;
        }}
        QPushButton:hover {{
            border-color: #888;
        }}
        QPushButton:checked:hover {{
            border-color: #ffaa00;
        }}
    """


def command_button_style() -> str:
    return """
        QPushButton {
            background-color: #2d2d2d;
            color: #eeeeee;
            border: 2px solid #555;
            border-radius: 4px;
            min-width: 110px;
            min-height: 40px;
            padding: 4px 10px;
        }
        QPushButton:checked {
            background-color: #1a4a8a;
            border: 5px solid #5aa8ff;
            color: #ffffff;
        }
        QPushButton:hover {
            border-color: #888;
        }
    """


def action_button_style(accent: str) -> str:
    return f"""
        QPushButton {{
            background-color: {accent};
            color: #ffffff;
            border: none;
            border-radius: 4px;
            min-width: 100px;
            min-height: 44px;
            font-weight: bold;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: #ffffff20;
        }}
        QPushButton:pressed {{
            background-color: #00000040;
        }}
    """


def preset_button_style() -> str:
    """Style for non-checkable quick-fill buttons (haptic patterns / period presets)."""
    return """
        QPushButton {
            background-color: #383838;
            color: #dddddd;
            border: 1px solid #555;
            border-radius: 4px;
            min-width: 90px;
            min-height: 36px;
            padding: 2px 8px;
        }
        QPushButton:hover {
            background-color: #484848;
            border-color: #888;
        }
        QPushButton:pressed {
            background-color: #1a4a8a;
        }
    """
