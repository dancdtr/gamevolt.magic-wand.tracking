from __future__ import annotations

from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from gamevolt.tcp.tcp_client import TcpClient
from wand.streaming.eliko.configuration.eliko_connection_settings import ElikoConnectionSettings


class ElikoClient:
    def __init__(self, logger: Logger, settings: ElikoConnectionSettings, client: TcpClient) -> None:
        self._settings = settings
        self._logger = logger

        self._tcp = client

        # self._tcp = TcpClient(
        #     logger=logger,
        #     settings=TcpClientSettings(
        #         host=settings.host,
        #         port=settings.port,
        #         reconnect_delay_s=settings.reconnect_delay_s,
        #     ),
        # )
        self._request = f"$PEKIO,SET_REPORT_LIST,{settings.report_type}\r\n"
        self._tcp.connected.subscribe(self._on_connected)

    @property
    def line_received(self) -> Event[Callable[[str], None]]:
        return self._tcp.line_received

    async def start_async(self) -> None:
        await self._tcp.start_async()

    async def stop_async(self) -> None:
        await self._tcp.stop_async()

    def send_command(self, command: str) -> None:
        self._tcp.send(command)

    def _on_connected(self) -> None:
        self._logger.info(f"Eliko client requesting {self._settings.report_type} reports")
        self._tcp.send(self._request)
