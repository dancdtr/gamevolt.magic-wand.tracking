import logging
from typing import Callable

from gamevolt.logging import Logger
from wand.configuration.wand_server_settings import WandServerSettings
from wand.wand_client import WandClient
from wand.wand_id_filter import WandIdFilter
from wand.wand_rotation_raw import WandRotationRaw


class WandClientRegistry:
    def __init__(
        self,
        logger: Logger,
        settings: WandServerSettings,
        wand_filter: WandIdFilter,
        on_connected: Callable[[WandClient], None],
        on_disconnected: Callable[[WandClient], None],
        on_rotation_raw: Callable[[WandRotationRaw], None],
    ) -> None:
        self._logger = logger
        self._settings = settings
        self._filter = wand_filter
        self._clients: dict[str, WandClient] = {}

        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._on_rotation_raw = on_rotation_raw

    def snapshot(self) -> list[WandClient]:
        return list(self._clients.values())

    def clear(self) -> None:
        for client in list(self._clients.values()):
            client.wand_rotation_raw_updated.unsubscribe(self._on_rotation_raw)
        self._clients.clear()

    def get_or_create(self, client_id: str) -> WandClient | None:
        client_id = client_id.upper()
        existing = self._clients.get(client_id)
        if existing is not None:
            return existing

        if not self._filter.allows(client_id):
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(f"Ignoring wand {client_id}. filter_wands=True and id not in allowlist.")
            return None

        self._logger.info(f"Client ({client_id}) connected.")
        client = WandClient(
            logger=self._logger,
            id=client_id,
            disconnect_after_s=self._settings.disconnect_after_s,
        )
        self._clients[client_id] = client

        self._on_connected(client)
        client.wand_rotation_raw_updated.subscribe(self._on_rotation_raw)
        return client

    def prune_disconnected(self, now: float) -> None:
        if not self._clients:
            return

        to_remove: list[str] = []
        for client_id, client in list(self._clients.items()):
            if not client.is_connected(now):
                self._logger.info(f"Client ({client_id}) disconnected.")
                to_remove.append(client_id)

        for client_id in to_remove:
            client = self._clients.pop(client_id, None)
            if client is None:
                continue
            client.wand_rotation_raw_updated.unsubscribe(self._on_rotation_raw)
            self._on_disconnected(client)
