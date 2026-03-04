import logging
from logging import Logger
from typing import Callable

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
        cid = client_id.upper()
        existing = self._clients.get(cid)
        if existing is not None:
            return existing

        if not self._filter.allows(cid):
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(f"Ignoring wand {cid}. filter_wands=True and id not in allowlist.")
            return None

        self._logger.info(f"Client ({cid}) connected.")
        client = WandClient(
            logger=self._logger,
            settings=self._settings.client,
            id=cid,
            disconnect_after_s=self._settings.disconnect_after_s,
        )
        self._clients[cid] = client

        self._on_connected(client)
        client.wand_rotation_raw_updated.subscribe(self._on_rotation_raw)
        return client

    def prune_disconnected(self, now: float) -> None:
        if not self._clients:
            return

        to_remove: list[str] = []
        for cid, client in list(self._clients.items()):
            if not client.is_connected(now):
                self._logger.info(f"Client ({cid}) disconnected.")
                to_remove.append(cid)

        for cid in to_remove:
            client = self._clients.pop(cid, None)
            if client is None:
                continue
            client.wand_rotation_raw_updated.unsubscribe(self._on_rotation_raw)
            self._on_disconnected(client)
