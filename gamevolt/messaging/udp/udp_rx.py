from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from logging import Logger
from typing import Any

from gamevolt.events.event import Event
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings


class UdpRx:
    def __init__(self, logger: Logger, settings: UdpRxSettings) -> None:
        self._datagram_received: Event[Callable[[str, tuple[str, int]], None]] = Event()
        self._message_received: Event[Callable[[str], None]] = Event()

        self._settings = settings
        self._logger = logger

        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: asyncio.DatagramProtocol | None = None

    @property
    def datagram_received(self) -> Event[Callable[[str, tuple[str, int]], None]]:
        return self._datagram_received

    @property
    def message_received(self) -> Event[Callable[[str], None]]:
        return self._message_received

    async def start_async(self) -> None:
        if self._transport is not None:
            self._logger.warning("UdpRx already started.")
            return

        loop = asyncio.get_running_loop()

        class _Proto(asyncio.DatagramProtocol):
            def datagram_received(proto_self, data: bytes, addr: tuple[str, int]) -> None:
                try:
                    if len(data) > self._settings.max_size:
                        self._logger.warning(f"UDP datagram too large from {addr}")
                        return

                    text = data.decode("utf-8", errors="replace")

                    self._message_received.invoke(text)
                    self._datagram_received.invoke(text, addr)

                except Exception as exc:
                    self._logger.warning(f"UDP error from {addr}: {exc} (raw={data!r})")

        self._transport, self._protocol = await loop.create_datagram_endpoint(
            lambda: _Proto(),
            local_addr=(self._settings.host, self._settings.port),
        )

        self._logger.info(f"UdpRx listening on udp://{self._settings.host}:{self._settings.port}")

    async def stop_async(self) -> None:
        if self._transport is None:
            return
        self._transport.close()
        self._transport = None
        self._protocol = None
        self._logger.info("UdpRx stopped.")
