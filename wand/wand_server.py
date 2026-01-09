from __future__ import annotations

import re
import time
from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.serial.serial_receiver import SerialReceiver
from wand.configuration.wand_server_settings import WandServerSettings
from wand.wand_client import WandClient
from wand.wand_rotation_raw import WandRotationRaw


class WandServer:
    """
    - Receives serial lines in PKT/DATA pairs (matched by seq).
    - Creates a WandClient on first seen tag id (optionally filtered by wand_ids).
    - Removes a WandClient if it has not been seen for disconnect_after_s.
    """

    _PKT_RE = re.compile(
        r"^PKT\s+t_rx=(?P<t_rx>\d+)\s+t_base=(?P<t_base>\d+)\s+tag=(?P<tag>[0-9A-Fa-f]+)\s+seq=(?P<seq>\d+)\s+nsamp=(?P<nsamp>\d+)\s*$"
    )
    _DATA_RE = re.compile(r'^(?:DATA|DATA_RAW)\s+seq=(?P<seq>\d+)\s+data="?(?P<data>.*)"?\s*$')

    def __init__(self, logger: Logger, settings: WandServerSettings) -> None:
        self._logger = logger
        self._settings = settings

        self._serial = SerialReceiver(logger=logger, settings=settings.serial_receiver)

        self._connected_clients: dict[str, WandClient] = {}

        # Pair DATA with PKT via seq:
        # seq -> (t_base_ms, tag_hex, nsamp, monotonic_received)
        self._pending_headers: dict[int, tuple[int, str, int, float]] = {}

        self.wand_rotation_raw_updated: Event[Callable[[WandRotationRaw], None]] = Event()
        self.wand_connected: Event[Callable[[WandClient], None]] = Event()
        self.wand_disconnected: Event[Callable[[WandClient], None]] = Event()

    # ── lifecycle ────────────────────────────────────────────────────────────

    async def start(self) -> None:
        self._logger.info("Starting wand server...")
        self._serial.data_received.subscribe(self._on_line)
        await self._serial.start()

    async def stop(self) -> None:
        self._serial.data_received.unsubscribe(self._on_line)
        await self._serial.stop()

        self._pending_headers.clear()

        # Clean up clients
        for client in list(self._connected_clients.values()):
            client.wand_rotation_raw_updated.unsubscribe(self._on_wand_rotation_raw_updated)
        self._connected_clients.clear()

    def update(self) -> None:
        now = time.monotonic()
        self._prune_pending_headers(now)
        self._prune_disconnected_clients(now)

    # ── public helpers ───────────────────────────────────────────────────────

    def connected_clients(self) -> list[WandClient]:
        """Snapshot of currently connected clients (do not mutate)."""
        return list(self._connected_clients.values())

    # ── internal ─────────────────────────────────────────────────────────────

    def _prune_pending_headers(self, now: float) -> None:
        if not self._pending_headers:
            return

        ttl = float(self._settings.header_ttl_s)
        expired = [seq for seq, (_, _, _, t0) in self._pending_headers.items() if (now - t0) > ttl]
        for seq in expired:
            self._pending_headers.pop(seq, None)

    def _get_or_create_client(self, client_id: str) -> WandClient | None:
        client_id = client_id.upper()

        client = self._connected_clients.get(client_id)
        if client is not None:
            return client

        if self._settings.filter_wands and client_id not in self._settings.filtered_wand_ids:
            return None

        self._logger.info(f"Client ({client_id}) connected.")

        client = WandClient(
            logger=self._logger,
            settings=self._settings.client,
            id=client_id,
            disconnect_after_s=self._settings.disconnect_after_s,
        )

        self._connected_clients[client_id] = client

        self.wand_connected.invoke(client)
        client.wand_rotation_raw_updated.subscribe(self._on_wand_rotation_raw_updated)

        return client

    def _prune_disconnected_clients(self, now: float) -> None:
        if not self._connected_clients:
            return

        to_remove: list[str] = []
        for id, client in list(self._connected_clients.items()):
            if not client.is_connected(now):
                self._logger.info(f"Client ({id}) disconnected.")
                to_remove.append(id)

        for id in to_remove:
            client = self._connected_clients.pop(id, None)
            if client is None:
                continue
            client.wand_rotation_raw_updated.unsubscribe(self._on_wand_rotation_raw_updated)
            self.wand_disconnected.invoke(client)

    # ── serial parsing ───────────────────────────────────────────────────────

    def _on_line(self, line: str) -> None:
        if not line:
            return

        line = line.strip()  # IMPORTANT: handles CRLF (\r\n) from serial
        if not line:
            return

        now = time.monotonic()

        # PKT header
        m = self._PKT_RE.match(line)
        if m:
            seq = int(m["seq"])
            t_base = int(m["t_base"])
            tag_hex = m["tag"].upper()
            nsamp = int(m["nsamp"])
            self._pending_headers[seq] = (t_base, tag_hex, nsamp, now)
            return

        # DATA batch
        m = self._DATA_RE.match(line)
        if not m:
            return

        seq = int(m["seq"])
        data_str = m["data"].strip()

        header = self._pending_headers.pop(seq, None)
        if header is None:
            return  # no header => can't route DATA to a tag/t_base

        t_base, tag_hex, _nsamp, _t0 = header

        client = self._get_or_create_client(tag_hex)
        if client is None:
            return

        client.on_wand_rotation_data(t_base, data_str)

    def _on_wand_rotation_raw_updated(self, msg: WandRotationRaw) -> None:
        self.wand_rotation_raw_updated.invoke(msg)
