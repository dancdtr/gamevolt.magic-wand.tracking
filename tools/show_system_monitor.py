#!/usr/bin/env python3
"""Standalone UDP listener for the external show-system feed.

The app's ShowSystemController sends one JSON datagram per recognised cast
(`ShowSystemSpellCastMessage`: spell_type / quality / house, enums as names) to the
host:port of a destination configured under `show_system_controller.destinations`
in appsettings.yml. Run this to prove the right data is going out.

Local use: point that `host` at this machine (e.g. 127.0.0.1) and run:

    uv run python tools/show_system_monitor.py            # binds 0.0.0.0:6006
    uv run python tools/show_system_monitor.py --port 6006 --host 0.0.0.0

No project imports — pure stdlib, so it stays runnable even mid-refactor.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from datetime import datetime

# Known message fields worth pulling into the one-line summary, in display order.
_SUMMARY_FIELDS = ("MessageType", "spell_type", "quality", "house", "wand_id")


def _summary(payload: dict) -> str:
    parts = [f"{k}={payload[k]}" for k in _SUMMARY_FIELDS if k in payload]
    return "  ".join(parts) if parts else "(no known fields)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Listen for show-system UDP messages and print them.")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default: 0.0.0.0 = all interfaces)")
    parser.add_argument("--port", type=int, default=6006, help="bind port (default: 6006)")
    parser.add_argument("--raw", action="store_true", help="also print the raw datagram bytes")
    args = parser.parse_args()

    # Line-buffer stdout so a live feed shows up immediately even when piped/redirected.
    sys.stdout.reconfigure(line_buffering=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.host, args.port))

    print(f"show-system monitor listening on udp://{args.host}:{args.port}  (Ctrl-C to stop)\n")

    try:
        while True:
            data, sender = sock.recvfrom(65535)
            stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            src = f"{sender[0]}:{sender[1]}"

            try:
                payload = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                print(f"[{stamp}] {src}  <non-JSON {len(data)}B> {data!r}")
                continue

            if isinstance(payload, dict):
                print(f"[{stamp}] {src}  {_summary(payload)}")
                for key, val in payload.items():
                    if key not in _SUMMARY_FIELDS:
                        print(f"             {key}: {val}")
            else:
                print(f"[{stamp}] {src}  {payload}")

            if args.raw:
                print(f"             raw: {data!r}")
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
