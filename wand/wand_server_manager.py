from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from wand.wand_client import WandClient
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server import WandServer
from wand.wand_server_protocol import WandServerProtocol


class WandServerManager(WandServerProtocol):
    def __init__(self, logger: Logger, servers: list[WandServer]) -> None:
        self._wand_rotation_raw_updated: Event[Callable[[WandRotationRaw], None]] = Event()
        self._wand_disconnected: Event[Callable[[WandClient], None]] = Event()
        self._wand_connected: Event[Callable[[WandClient], None]] = Event()

        self._servers = servers
        self._logger = logger

    @property
    def wand_rotation_raw_updated(self) -> Event[Callable[[WandRotationRaw], None]]:
        return self._wand_rotation_raw_updated

    @property
    def wand_disconnected(self) -> Event[Callable[[WandClient], None]]:
        return self._wand_disconnected

    @property
    def wand_connected(self) -> Event[Callable[[WandClient], None]]:
        return self._wand_connected

    async def start(self) -> None:
        for server in self._servers:
            server.wand_rotation_raw_updated.subscribe(self._wand_rotation_raw_updated.invoke)
            server.wand_disconnected.subscribe(self._wand_disconnected.invoke)
            server.wand_connected.subscribe(self._wand_connected.invoke)

        for server in self._servers:
            await server.start()

    async def stop(self) -> None:
        for server in self._servers:
            await server.stop()

        for server in self._servers:
            server.wand_rotation_raw_updated.unsubscribe(self._wand_rotation_raw_updated.invoke)
            server.wand_disconnected.unsubscribe(self._wand_disconnected.invoke)
            server.wand_connected.unsubscribe(self._wand_connected.invoke)
