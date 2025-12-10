# wand_client.py

from __future__ import annotations

import re
from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.serial.serial_receiver import SerialReceiver
from wand.configuration.input_settings import InputSettings
from wand.configuration.wand_server_settings import WandServerSettings
from wand.wand_client import WandClient
from wand.wand_rotation_raw import WandRotationRaw


class WandServer:
    """
    Parses anchor output:
      PKT t_rx=... t_base=... tag=E001 seq=141 nsamp=12
      DATA seq=141 data=-1013,-271; -1013,-271; ...

    - Takes first two ints in each item as yaw100,pitch100 (centi-deg) → degrees.
    - Synthesizes per-sample timestamps: ms = t_base + i*(1000/imu_hz).
    - Optional resample to target_hz per client. Set target_hz=None/0 to emit all.
    """

    _PKT_RE = re.compile(
        r"^PKT\s+t_rx=(?P<t_rx>\d+)\s+t_base=(?P<t_base>\d+)\s+tag=(?P<tag>[0-9A-Fa-f]+)\s+seq=(?P<seq>\d+)\s+nsamp=(?P<nsamp>\d+)\s*$"
    )
    _DATA_RE = re.compile(r'^(?:DATA|DATA_RAW)\s+seq=(?P<seq>\d+)\s+data="?(?P<data>.*)"?\s*$')

    def __init__(
        self,
        logger: Logger,
        input_settings: InputSettings,
        server_settings: WandServerSettings,
    ) -> None:
        self._server_settings = server_settings
        self._logger = logger

        self._serial = SerialReceiver(logger=logger, settings=server_settings.serial_receiver)

        # Create one WandClient per tracked wand id
        self._connected_clients: dict[str, WandClient] = {}
        for wand in input_settings.tracked_wands:
            tag_hex = wand.id.upper()
            client = WandClient(logger, server_settings.client, tag_hex)
            client.wand_rotation_raw_updated.subscribe(self._on_wand_rotation_raw_updated)
            self._connected_clients[tag_hex] = client

        # Pair DATA with PKT via seq: seq -> (t_base_ms, tag_hex, nsamp)
        self._pending_headers: dict[int, tuple[int, str, int]] = {}

        # Aggregate event from all clients
        self.wand_rotation_raw_updated: Event[Callable[[WandRotationRaw], None]] = Event()

    # ── lifecycle ────────────────────────────────────────────────────────────
    async def start(self) -> None:
        await self._serial.start()
        self._logger.info("Starting wand server...")
        self._serial.data_received.subscribe(self._on_line)

    async def stop(self) -> None:
        self._serial.data_received.unsubscribe(self._on_line)

        await self._serial.stop()
        self._pending_headers.clear()

        for client in self._connected_clients.values():
            client.wand_rotation_raw_updated.unsubscribe(self._on_wand_rotation_raw_updated)

    # ── internal parsing ─────────────────────────────────────────────────────
    def _on_line(self, line: str) -> None:
        if not line:
            return

        # PKT header
        m = self._PKT_RE.match(line)
        if m:
            seq = int(m["seq"])
            t_base = int(m["t_base"])
            tag_hex = m["tag"].upper()
            nsamp = int(m["nsamp"])
            self._pending_headers[seq] = (t_base, tag_hex, nsamp)
            return

        # DATA batch
        m = self._DATA_RE.match(line)
        if not m:
            return

        seq = int(m["seq"])
        data_str = m["data"].strip()

        t_base, tag_hex, _ = self._pending_headers.pop(seq, (0, "????", 0))

        client = self._connected_clients.get(tag_hex)
        if client is None:
            # unknown tag, ignore
            return

        client.on_wand_rotation_data(t_base, data_str)

    # # ── aggregate emit ───────────────────────────────────────────────────────
    def _on_wand_rotation_raw_updated(self, msg: WandRotationRaw) -> None:
        self.wand_rotation_raw_updated.invoke(msg)
        # If you want to log at server level too:
        # self._logger.debug(f"SERVER EMIT {msg.id} @ {msg.ms} ms")
