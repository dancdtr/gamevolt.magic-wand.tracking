# gamevolt/messaging/udp/udp_tx.py
import json
import socket
from typing import Any

from gamevolt.logging import Logger
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings


class UdpTx:
    def __init__(self, logger: Logger, settings: UdpTxSettings):
        self._logger = logger
        self._settings = settings

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._sequence_id = 0

    def send(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_bytes(data)

    def send_str(self, payload: str) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_bytes(data)

    def send_bytes(self, encoded: bytes) -> None:
        self._logger.trace(f"Sending to 'udp://{self._settings.address}': {bytes}")
        self._sock.sendto(encoded, self._settings.address)
