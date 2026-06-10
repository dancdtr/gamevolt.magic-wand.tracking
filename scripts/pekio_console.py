"""Interactive PEKIO command console for the Eliko single-anchor over USB-serial.

Run:
    uv run python scripts/pekio_console.py
    uv run python scripts/pekio_console.py --port /dev/tty.usbmodem2101 --tag 0x1DAE --quiet

Stop wands_app first — only one process can hold the serial port.

Drops into a Python REPL with helper functions bound from a `PekioClient`
instance. Inbound lines from the anchor stream into the same terminal on a
background thread.

Quick reference:
    solid(RED)                           # solid red
    solid(RED | GREEN | BLUE)            # combine via bitwise OR
    solid(YELLOW)                        # pre-combined alias
    blink_fast(BLUE)                     # period 100ms, duty 15ms
    blink_medium(GREEN)                  # period 500ms, duty 100ms
    blink_slow(RED)                      # period 2550ms, duty 255ms
    blink(500, 255, BLUE)                # custom timing
    fade_slow(GREEN)                     # step=3 (doc "slow green fade")
    fade_medium(MAGENTA)                 # step=16
    fade_fast(WHITE)                     # step=38 (doc "fast white fade")
    fade(3, GREEN)                       # custom step
    hwave(16)                            # one-shot haptic, waveform 16
    hwave(82, 70)                        # waveforms 82 + 70
    stop()                               # all off

Timed (auto-stops after duration):
    pulse(RED, 2.0)                      # red on for 2s, then off
    pulse(RED, 2.0, haptic=True)         # red + haptic for 2s
    blink_fast_for(2.0, BLUE)            # fast-blink blue for 2s
    blink_for(2.0, 500, 255, GREEN)      # custom blink for 2s
    fade_slow_for(3.0, MAGENTA)          # slow fade for 3s
    fade_fast_for(2.0, WHITE)            # fast fade for 2s
    fade_for(3.0, 3, MAGENTA)            # custom-step fade for 3s
    cancel_timed()                       # cancel any pending auto-stop

Notes:
    Any plain command (solid, blink, etc.) sent during a timed effect cancels
    the pending stop — so you can override mid-pulse without orphan timers.

Other:
    raw('0x0A0F0002')                    # arbitrary CMD1 param
    cmd0(2)                              # CMD0 preset 2 (red 25%)
    spqf('R'), spqf('P')                 # toggle PR (IMU) <-> RR stream
    tag('0x1DC6')                        # switch target tag
"""

from __future__ import annotations

import argparse
import code
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import serial  # noqa: E402

from wand.streaming.eliko.pekio_client import (  # noqa: E402
    BUZZ_PATTERN_1,
    BUZZ_PATTERN_2,
    BUZZ_PATTERN_3,
    BUZZ_PATTERN_4,
    BUZZ_PATTERN_5,
    Colour,
    PekioClient,
)

DEFAULT_PORT = "/dev/tty.usbmodem2101"
DEFAULT_BAUD = 115200
DEFAULT_TAG = "0x1DAE"


def _reader_loop(ser: serial.Serial) -> None:
    while ser.is_open:
        try:
            line = ser.readline()
            if line:
                sys.stdout.write(line.decode("utf-8", errors="replace"))
                sys.stdout.flush()
        except Exception:
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive PEKIO command console for the Eliko single-anchor over USB-serial.")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Send SPQF,R on startup to quiet the PR firehose.",
    )
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.5)
    print(f"Connected to {args.port} @ {args.baud} baud. Default tag={args.tag}.")
    print("Functions: solid, blink, blink_fast/medium/slow, fade, fade_slow/medium/fast, buzz, buzz_fast/medium/slow, hwave, stop, raw, cmd0, spqf, tag.")
    print("Timed:     pulse, blink_for, blink_fast/medium/slow_for, fade_for, fade_slow/medium/fast_for, cancel_timed.")
    print("Buzz arg:  any LED method takes buzz='fast'|'medium'|'slow'|int(ms)|True|None.")
    print("Patterns: BUZZ_PATTERN_1..5 (waveform tuples — unpack with `*`).")
    print("Colours:  RED GREEN BLUE WHITE (single)")
    print("         YELLOW MAGENTA CYAN RGB (RGB combos)")
    print("         PINK LIME SKY WARM_WHITE PURPLE ICE ALL (W-combos — try and see)")
    print("         Combine any with `|`, e.g. RED | WHITE.")
    print("Type `help(blink)` for any one. Ctrl-D to exit.\n")

    def send(line: str) -> None:
        print(f">>> {line}")
        ser.write((line + "\r\n").encode("utf-8"))

    client = PekioClient(send_line=send, tag=args.tag)

    reader = threading.Thread(target=_reader_loop, args=(ser,), daemon=True)
    reader.start()

    if args.quiet:
        client.spqf("R")

    namespace = {
        # Client methods exposed as bare names.
        "solid": client.solid,
        "blink": client.blink,
        "blink_fast": client.blink_fast,
        "blink_medium": client.blink_medium,
        "blink_slow": client.blink_slow,
        "fade": client.fade,
        "fade_slow": client.fade_slow,
        "fade_medium": client.fade_medium,
        "fade_fast": client.fade_fast,
        "buzz": client.buzz,
        "buzz_fast": client.buzz_fast,
        "buzz_medium": client.buzz_medium,
        "buzz_slow": client.buzz_slow,
        "hwave": client.hwave,
        "hwave_oneshot": client.hwave_oneshot,
        "buzz_hwave": client.buzz_hwave,
        "buzz_hwave_stop": client.buzz_hwave_stop,
        "pulse": client.pulse,
        "blink_for": client.blink_for,
        "blink_fast_for": client.blink_fast_for,
        "blink_medium_for": client.blink_medium_for,
        "blink_slow_for": client.blink_slow_for,
        "fade_for": client.fade_for,
        "fade_slow_for": client.fade_slow_for,
        "fade_medium_for": client.fade_medium_for,
        "fade_fast_for": client.fade_fast_for,
        "cancel_timed": client.cancel_timed,
        "stop": client.stop,
        "stop_led": client.stop_led,
        "stop_all": client.stop_all,
        "raw": client.raw,
        "cmd0": client.cmd0,
        "cmd1": client.cmd1,
        "spqf": client.spqf,
        "tag": client.set_tag,
        # Client itself, for direct access.
        "client": client,
        # Colours.
        "Colour": Colour,
        "BUZZ_PATTERN_1": BUZZ_PATTERN_1,
        "BUZZ_PATTERN_2": BUZZ_PATTERN_2,
        "BUZZ_PATTERN_3": BUZZ_PATTERN_3,
        "BUZZ_PATTERN_4": BUZZ_PATTERN_4,
        "BUZZ_PATTERN_5": BUZZ_PATTERN_5,
        "RED": Colour.RED,
        "GREEN": Colour.GREEN,
        "BLUE": Colour.BLUE,
        "WHITE": Colour.WHITE,
        "YELLOW": Colour.YELLOW,
        "MAGENTA": Colour.MAGENTA,
        "CYAN": Colour.CYAN,
        "RGB": Colour.RGB,
        "PINK": Colour.PINK,
        "LIME": Colour.LIME,
        "SKY": Colour.SKY,
        "WARM_WHITE": Colour.WARM_WHITE,
        "PURPLE": Colour.PURPLE,
        "ICE": Colour.ICE,
        "ALL": Colour.ALL,
    }
    try:
        code.interact(banner="", local=namespace)
    finally:
        ser.close()


if __name__ == "__main__":
    main()
