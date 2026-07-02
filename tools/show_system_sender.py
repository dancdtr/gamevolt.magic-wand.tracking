#!/usr/bin/env python3
"""Send a fake spell-cast to a show-system destination over UDP.

Bypasses wand tracking / recognition entirely. Builds the exact wire payload
ShowSystemController emits (ShowSystemSpellCastMessage.to_dict, compact JSON)
and fires it at the forshaw box, to prove the UDP path works.

Usage:
    python3 tools/show_system_sender.py                         # one INCENDIO to forshaw
    python3 tools/show_system_sender.py --spell RICTUSEMPRA
    python3 tools/show_system_sender.py --host 192.168.1.118 --port 6006
    python3 tools/show_system_sender.py --count 5 --interval 1.0 --spell ALOHOMORA
"""
import argparse
import json
import socket
import time
from datetime import datetime

# Mirrors ShowSystemController routing list for forshaw_show_system.
SPELLS = ["RICTUSEMPRA", "ALOHOMORA", "COLLOPORTUS", "CANTIS", "PEPPER_BREATH_HEX", "INCENDIO", "EXTINGUISHING_SPELL"]
QUALITIES = ["RUDIMENTARY", "SKILLED", "EXPERIENCED", "MASTERED"]
HOUSES = ["UNASSIGNED", "GRYFFINDOR", "RAVENCLAW", "HUFFLEPUFF", "SLYTHERIN"]


def build_payload(spell: str, quality: str, house: str, wand_id: str) -> dict:
    return {
        "Timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "MessageType": "ShowSystemSpellCastMessage",
        "spell_type": spell,
        "quality": quality,
        "house": house,
        "wand_id": wand_id,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fake show-system UDP sender")
    parser.add_argument("--host", default="192.168.1.118", help="destination IP (default forshaw 192.168.1.118)")
    parser.add_argument("--port", type=int, default=6006, help="destination port (default 6006)")
    parser.add_argument("--spell", default="INCENDIO", choices=SPELLS)
    parser.add_argument("--quality", default="MASTERED", choices=QUALITIES)
    parser.add_argument("--house", default="GRYFFINDOR", choices=HOUSES)
    parser.add_argument("--wand-id", default="0x001DA5", help="wand id (default 0x001DA5)")
    parser.add_argument("--count", type=int, default=1, help="number of packets")
    parser.add_argument("--interval", type=float, default=0.5, help="seconds between packets")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = (args.host, args.port)

    for i in range(args.count):
        payload = build_payload(args.spell, args.quality, args.house, args.wand_id)
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        sock.sendto(data, dest)
        print(f"[{i + 1}/{args.count}] -> udp://{args.host}:{args.port}  {data.decode()}")
        if i + 1 < args.count:
            time.sleep(args.interval)

    print("Done.")


if __name__ == "__main__":
    main()
