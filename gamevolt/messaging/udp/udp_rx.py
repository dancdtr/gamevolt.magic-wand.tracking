from __future__ import annotations

import socket
import threading
from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings


class UdpRx:
    """
    UDP receiver that raises an event with each received datagram as a UTF-8 string.

    - Background thread only (no foreground iterator).
    - No JSON parsing; next layer (e.g., GestureRx) can parse and map to domain types.
    - Uses your Event[Callable[[str], None]] for subscribers.

    Subscribe:
        rx = UdpRx(port=9999)
        rx.message_received.subscribe(lambda s: print("RX ←", s))
        rx.start()
        ...
        rx.stop()
    """

    def __init__(self, logger: Logger, settings: UdpRxSettings) -> None:
        self._logger = logger
        self._settings = settings

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(self._settings.address)
        self._sock.settimeout(self._settings.recv_timeout_s)

        self._running = threading.Event()
        self._thread: threading.Thread | None = None

        self.message_received: Event[Callable[[str], None]] = Event()

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._running.set()
        self._thread = threading.Thread(target=self._run_loop, name="UdpRx", daemon=True)
        self._thread.start()
        self._logger.info(f"UdpRx listening on udp://{self._settings.host}:{self._settings.port}...")

    def stop(self) -> None:
        """Stop the loop and close the socket."""
        self._logger.info(f"Stopping UdpRx listening on udp://{self._settings.host}:{self._settings.port}...")
        self._running.clear()
        try:
            # Nudge the blocking recv with a short timeout
            self._sock.settimeout(0.05)
        except OSError:
            pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        try:
            self._sock.close()
        except OSError:
            pass

        self._logger.info(f"UdpRx stopped listening on udp://{self._settings.host}:{self._settings.port}.")

    def close(self) -> None:
        self.stop()

    def __enter__(self) -> UdpRx:
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def _run_loop(self) -> None:
        while self._running.is_set():
            try:
                data, _addr = self._sock.recvfrom(self._settings.max_size)
            except socket.timeout:
                continue
            except OSError:
                break  # socket closed

            text = data.decode("utf-8", errors="replace")

            try:
                self.message_received.invoke(text)
            except Exception as e:
                self._logger.exception(f"Exception in UdpRx: {e}")
