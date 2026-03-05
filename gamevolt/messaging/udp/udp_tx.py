# gamevolt/messaging/udp/udp_tx.py
import json
import socket
from logging import Logger
from typing import Any

from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings


class UdpTx:
    def __init__(self, logger: Logger, settings: UdpTxSettings):
        self._logger = logger
        self._settings = settings

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._sequence_id = 0

    def send(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        self._logger.debug(f"Sending to 'udp://{self._settings.address}': {data}")
        self._sock.sendto(data, self._settings.address)

    def send_str(self, payload: str) -> None:
        data = json.dumps(payload).encode("utf-8")
        self._logger.info(f"Sending to 'udp://{self._settings.address}': {data}")
        self._sock.sendto(data, self._settings.address)
