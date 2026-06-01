from __future__ import annotations

import time
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from wand.configuration.wand_server_settings import WandServerSettings
from wand.data.assembled_packet import AssembledPacket
from wand.streaming.wand_imu_stream import WandImuStream
from wand.wand_client import WandClient
from wand.wand_client_registry import WandClientRegistry
from wand.wand_id_filter import WandIdFilter
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server_protocol import WandServerProtocol


class WandServer(WandServerProtocol):
    def __init__(
        self,
        logger: Logger,
        settings: WandServerSettings,
        imu_stream: WandImuStream,
        tracked_wand_ids: list[str],
    ) -> None:
        self._wand_rotation_raw_updated: Event[Callable[[WandRotationRaw], None]] = Event()
        self._wand_disconnected: Event[Callable[[WandClient], None]] = Event()
        self._wand_connected: Event[Callable[[WandClient], None]] = Event()

        self._imu_stream = imu_stream
        self._settings = settings
        self._logger = logger

        self._filter = WandIdFilter(allowed_ids=tracked_wand_ids)

        self._registry = WandClientRegistry(
            logger=logger,
            settings=settings,
            wand_filter=self._filter,
            on_connected=self._wand_connected.invoke,
            on_disconnected=self._wand_disconnected.invoke,
            on_rotation_raw=self._on_wand_rotation_raw_updated,
        )

    @property
    def wand_rotation_raw_updated(self) -> Event[Callable[[WandRotationRaw], None]]:
        return self._wand_rotation_raw_updated

    @property
    def wand_disconnected(self) -> Event[Callable[[WandClient], None]]:
        return self._wand_disconnected

    @property
    def wand_connected(self) -> Event[Callable[[WandClient], None]]:
        return self._wand_connected

    def start(self) -> None:
        self._logger.info("Starting wand server...")
        self._imu_stream.packet_received.subscribe(self._on_packet)
        self._logger.info(f"Started wand server. Allow list: {self._filter.snapshot()}")

    def stop(self) -> None:
        self._logger.info("Stopping wand server...")
        self._imu_stream.packet_received.unsubscribe(self._on_packet)
        self._registry.clear()
        self._logger.info("WandServer stopped.")

    def update(self) -> None:
        self._registry.prune_disconnected(time.monotonic())

    def add_wand_id(self, id: str) -> None:
        self._filter.add(id)

    def remove_wand_id(self, id: str) -> None:
        self._filter.remove(id)

    def connected_clients(self) -> list[WandClient]:
        return self._registry.snapshot()

    def _on_packet(self, packet: AssembledPacket) -> None:
        client = self._registry.get_or_create(packet.tag_hex)
        if client is None:
            self._logger.debug(f"DATA dropped (client filtered): tag={packet.tag_hex} seq={packet.seq}")
            return

        try:
            client.on_wand_rotation_data(packet.t0_ms, packet.sample_dt_us, packet.data_str)
        except Exception:
            self._logger.exception(
                f"Exception while routing wand data: tag={packet.tag_hex} seq={packet.seq} "
                f"t0={packet.t0_ms} dt_us={packet.sample_dt_us} fmt={packet.fmt} data_len={len(packet.data_str)}"
            )

    def _on_wand_rotation_raw_updated(self, msg: WandRotationRaw) -> None:
        self._logger.trace(f"wand_rotation_raw_updated: id={msg.id} ts={msg.ms} fx={msg.fx:.4f} fy={msg.fy:.4f} fz={msg.fz:.4f}")
        self.wand_rotation_raw_updated.invoke(msg)
