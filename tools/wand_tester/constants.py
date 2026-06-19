"""Shared constants for the wand LED/haptic GUI tester."""

from __future__ import annotations

from dataclasses import dataclass

from wand.streaming.eliko.pekio_client import Colour

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
    ColourOption("SINGLE WHITE", Colour.WHITE, "#ffffff", "#000000"),
    ColourOption("MAGENTA", Colour.MAGENTA, "#ff00ff", "#ffffff"),
    ColourOption("LIME", Colour.LIME, "#b8ff80", "#000000"),
    ColourOption("CYAN", Colour.CYAN, "#00e0e0", "#000000"),
    ColourOption("RGB WHITE", Colour.RGB, "#d0d0d0", "#000000"),
    ColourOption("PURPLE", Colour.PURPLE, "#c080ff", "#000000"),
    ColourOption("YELLOW", Colour.YELLOW, "#ffe000", "#000000"),
    ColourOption("SKY", Colour.SKY, "#80c0ff", "#000000"),
    ColourOption("FULL WHITE", Colour.ALL, "#f0f0f0", "#000000"),
    ColourOption("PINK", Colour.PINK, "#ffb0c8", "#000000"),
    ColourOption("WARM WHITE", Colour.WARM_WHITE, "#ffd890", "#000000"),
    ColourOption("ICE", Colour.ICE, "#c0f0ff", "#000000"),
    ColourOption("OFF", Colour.OFF, "#1a1a1a", "#cccccc"),
]

DEFAULT_COLOUR = "RED"

DEFAULT_BLINK_PERIOD_MS = 500
DEFAULT_BLINK_DUTY_MS = 100
DEFAULT_FADE_STEP = 8
DEFAULT_BLINK_FOR_DURATION_S = 2.0
DEFAULT_FADE_FOR_DURATION_S = 3.0

# Five-level LED speed presets, Slowest→Fastest. Replaces the old 3-level
# fast/medium/slow set. Blink period is firmware-capped at 2550ms (ZZ byte =
# period/10ms is one byte), so "Slowest" sits at that ceiling — the wand
# can't blink any slower. Fade step has full 1-255 headroom both ends.
BLINK_PRESETS: list[tuple[str, int, int]] = [  # (label, period_ms, duty_ms)
    ("Slowest", 2550, 255),
    ("Slow", 1200, 200),
    ("Medium", 500, 100),
    ("Fast", 150, 30),
    ("Fastest", 60, 12),
]
FADE_PRESETS: list[tuple[str, int]] = [  # (label, step) — lower step = slower
    ("Slowest", 1),
    ("Slow", 4),
    ("Medium", 8),
    ("Fast", 14),
    ("Fastest", 22),
]
BLINK_PRESETS_BY_NAME: dict[str, tuple[int, int]] = {label: (p, d) for label, p, d in BLINK_PRESETS}
FADE_PRESETS_BY_NAME: dict[str, int] = {label: step for label, step in FADE_PRESETS}

# A preset button's selection id is f"{prefix}:{label}" (e.g. "blink:Fast").
# Tabs parse the prefix to pick the client call and the label to look up the
# level's params in the tables above. Keeps the cross-section radio exclusive
# without one client method per level. Continuous-vs-timed is a per-section
# Loop checkbox in the LED tab, not part of the selection id.
BLINK_PREFIX = "blink"
FADE_PREFIX = "fade"


# Named haptic effects — wand-themed labels over the wand's haptic waveform
# library (TI DRV2605-style ids). The first group is verified on-wand (mirrors
# the BUZZ_PATTERN_* ids in pekio_client + scripts/pekio_commands.sh). The
# second group is exploratory: ids picked from the standard DRV2605 ROM
# library, names provisional until felt on real hardware. Each effect chains
# 1-3 waveforms back-to-back (hwave's 3-waveform limit).
HAPTIC_EFFECTS: list[tuple[str, tuple[int, ...]]] = [
    # Verified on-wand:
    ("Tap", (1,)),  # short tap
    ("Bump", (16,)),  # single bump
    ("Click Whirr", (82, 70)),  # two-waveform bump
    ("Triple Tap", (1, 1, 1)),  # rapid triple
    ("Spell Cast", (93, 14, 56)),  # three-waveform spell-cast chain
    # Exploratory (DRV2605 ROM ids — confirm on hardware, rename to taste):
    ("Click", (4,)),  # Sharp Click
    ("Soft Bump", (7,)),  # Soft Bump
    ("Double Click", (10,)),  # Double Click
    ("Buzz", (47,)),  # Buzz 1
    ("Tickle", (52,)),  # Pulsing Strong 1
    ("Hum", (64,)),  # Transition Hum 1
    ("Ramp Down", (70,)),  # Transition Ramp Down Long Smooth 1
    ("Sharp Tick", (24,)),  # Sharp Tick 1
    ("Strong Buzz", (14,)),  # Strong Buzz 100%
    ("Long Buzz", (118,)),  # long buzz (programmatic-stop effect)
]

# Haptic repeat-interval range for the Loop-mode slider.
PERIOD_MIN_MS = 500
PERIOD_MAX_MS = 8000
PERIOD_STEP_MS = 50
DEFAULT_PERIOD_MS = 2500
