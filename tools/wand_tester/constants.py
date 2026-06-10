"""Shared constants for the wand LED/haptic GUI tester."""

from __future__ import annotations

from dataclasses import dataclass

from wand.streaming.eliko.pekio_client import (
    BUZZ_MEDIUM_PERIOD_MS,
    BUZZ_PATTERN_1,
    BUZZ_PATTERN_2,
    BUZZ_PATTERN_3,
    BUZZ_PATTERN_4,
    BUZZ_PATTERN_5,
    Colour,
)

DEFAULT_PORT = "/dev/tty.usbmodem2101"
DEFAULT_BAUD = 115200

# Edit to add/remove known wand tags.
WAND_TAGS: list[str] = [
    "0x1DAE",
    "0x1DC6",
    "0x1DA5",
    "0x1DB0",
    "0x1DB1",
    "0x1DBA",
    "0x1DA7",
    "0x1DBF",
    "0x1DB6",
    "0x1DB7",
    "0x1DC3",
    "0x1DC5",
    "0x1DA8",
    "0x1DC9",
    "0x1DA9",
    "0x1DAA",
    "0x1DAB",
    "0x1D65",
    "0x1DAC",
    "0x1DAD",
    "0x1DB2",
]


@dataclass(frozen=True)
class ColourOption:
    name: str
    colour: Colour
    bg: str  # CSS hex for the button face
    fg: str  # CSS hex for label text (white on dark, black on light)


# Approximate visual swatches — wand LED mixing is RGB+W so these are
# indicative, not exact. Order drives grid layout.
COLOUR_OPTIONS: list[ColourOption] = [
    ColourOption("RED", Colour.RED, "#ff0000", "#ffffff"),
    ColourOption("GREEN", Colour.GREEN, "#00c800", "#ffffff"),
    ColourOption("BLUE", Colour.BLUE, "#0040ff", "#ffffff"),
    ColourOption("WHITE", Colour.WHITE, "#ffffff", "#000000"),
    ColourOption("MAGENTA", Colour.MAGENTA, "#ff00ff", "#ffffff"),
    ColourOption("LIME", Colour.LIME, "#b8ff80", "#000000"),
    ColourOption("CYAN", Colour.CYAN, "#00e0e0", "#000000"),
    ColourOption("RGB", Colour.RGB, "#d0d0d0", "#000000"),
    ColourOption("PURPLE", Colour.PURPLE, "#c080ff", "#000000"),
    ColourOption("YELLOW", Colour.YELLOW, "#ffe000", "#000000"),
    ColourOption("SKY", Colour.SKY, "#80c0ff", "#000000"),
    ColourOption("ALL", Colour.ALL, "#f0f0f0", "#000000"),
    ColourOption("PINK", Colour.PINK, "#ffb0c8", "#000000"),
    ColourOption("WARM_WHITE", Colour.WARM_WHITE, "#ffd890", "#000000"),
    ColourOption("ICE", Colour.ICE, "#c0f0ff", "#000000"),
    ColourOption("OFF", Colour.OFF, "#1a1a1a", "#cccccc"),
]

DEFAULT_COLOUR = "RED"

DEFAULT_BLINK_PERIOD_MS = 500
DEFAULT_BLINK_DUTY_MS = 100
DEFAULT_FADE_STEP = 8
DEFAULT_BLINK_FOR_DURATION_S = 2.0
DEFAULT_FADE_FOR_DURATION_S = 3.0

# Haptic preset sequences (waveform tuples) shown as quick-fill buttons.
HAPTIC_PATTERNS: list[tuple[str, tuple[int, ...]]] = [
    ("Pattern 1", BUZZ_PATTERN_1),
    ("Pattern 2", BUZZ_PATTERN_2),
    ("Pattern 3", BUZZ_PATTERN_3),
    ("Pattern 4", BUZZ_PATTERN_4),
    ("Pattern 5", BUZZ_PATTERN_5),
]

HAPTIC_MODE_ONESHOT = "oneshot"
HAPTIC_MODE_SEQUENCE = "sequence"
HAPTIC_MODE_ALARM = "alarm"

# LED methods that schedule an auto-stop. Excluded from reapply-after-haptic
# because re-firing would restart the duration timer on every haptic tick.
LED_TIMED_METHODS: frozenset[str] = frozenset(
    {
        "blink_for_custom",
        "blink_fast_for",
        "blink_medium_for",
        "blink_slow_for",
        "fade_for_custom",
        "fade_slow_for",
        "fade_medium_for",
        "fade_fast_for",
    }
)

# Haptic period slider range — shared by Haptic and LED+Haptic tabs.
PERIOD_MIN_MS = 500
PERIOD_MAX_MS = 8000
PERIOD_STEP_MS = 50
DEFAULT_PERIOD_MS = BUZZ_MEDIUM_PERIOD_MS
