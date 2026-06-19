#!/usr/bin/env python3
"""Dead-simple UDP receiver to prove spell casts reach the show system.

Listens on a UDP port and prints every datagram it receives. Point a
show-control destination (e.g. forshaw_show_system) at this host's IP and
this port to confirm the wands app is actually sending.

Usage:
    python3 tools/show_system_receiver.py            # listen on 0.0.0.0:6006
    python3 tools/show_system_receiver.py --port 6006 --host 0.0.0.0
"""
import argparse
import json
import socket
from datetime import datetime


def main() -> None:
    parser = argparse.ArgumentParser(description="UDP show-system receiver")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6006, help="bind port (default 6006)")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.host, args.port))

    print(f"Listening for UDP on {args.host}:{args.port} ... (Ctrl-C to quit)")

    while True:
        data, addr = sock.recvfrom(65535)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            payload = json.loads(data.decode("utf-8"))
            pretty = json.dumps(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pretty = repr(data)
        print(f"[{ts}] {addr[0]}:{addr[1]} -> {pretty}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
