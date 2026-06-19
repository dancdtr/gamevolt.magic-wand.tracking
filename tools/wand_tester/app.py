"""Application entry — argparse + serial port + QApplication wiring."""

from __future__ import annotations

import argparse
import sys
import threading

import serial
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from wand.streaming.eliko.pekio_client import PekioClient

from wand_tester.constants import DEFAULT_BAUD, DEFAULT_PORT, WAND_TAGS
from wand_tester.main_window import MainWindow
from wand_tester.styles import app_stylesheet


def _apply_dark_palette(app: QApplication) -> None:
    app.setStyle("Fusion")
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    p.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(120, 120, 120))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(120, 120, 120))
    app.setPalette(p)


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
    parser = argparse.ArgumentParser(description="PySide6 GUI tester for wand LED + haptic commands over USB-serial.")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument("--tag", default=WAND_TAGS[0])
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Send SPQF,R on startup to quiet the PR firehose.",
    )
    parser.add_argument(
        "--dark",
        action="store_true",
        help="Force Fusion dark palette (use on systems without OS dark mode, e.g. Raspberry Pi).",
    )
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.5)
    print(f"Connected to {args.port} @ {args.baud} baud. Default tag={args.tag}.")

    # Serialise writes — buzz_hwave fires from a Timer thread while the GUI main
    # thread can also send (Send/Stop clicks, tag changes). Without this lock the
    # byte streams interleave and the wand drops the garbled $PEKIO lines.
    write_lock = threading.Lock()

    def send(line: str) -> None:
        with write_lock:
            print(f">>> {line}")
            ser.write((line + "\r\n").encode("utf-8"))

    client = PekioClient(send_line=send, tag=args.tag)

    reader = threading.Thread(target=_reader_loop, args=(ser,), daemon=True)
    reader.start()

    if args.quiet:
        client.spqf("R")

    app = QApplication(sys.argv)
    if args.dark:
        _apply_dark_palette(app)
    # Arcane-theme skin sits on top of the palette so the look is consistent
    # across hosts (macOS native, Pi Fusion) regardless of --dark.
    app.setStyleSheet(app_stylesheet())
    window = MainWindow(client)
    window.show()
    try:
        sys.exit(app.exec())
    finally:
        ser.close()
