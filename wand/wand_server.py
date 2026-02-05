# wand/wand_server.py
from __future__ import annotations

import logging
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

        # Debug counters (logged periodically at DEBUG)
        self._lines_total = 0
        self._lines_pkt = 0
        self._lines_data = 0
        self._lines_unparsed = 0
        self._lines_orphan_data = 0
        self._lines_filtered = 0
        self._lines_empty = 0

        self._last_stats_log_monotonic = time.monotonic()
        self._stats_log_interval_s = 2.0

    # ── lifecycle ────────────────────────────────────────────────────────────

    async def start(self) -> None:
        self._logger.info("Starting wand server...")
        self._serial.data_received.subscribe(self._on_line)
        await self._serial.start()

        if self._logger.isEnabledFor(logging.DEBUG):
            filtered_ids = sorted([s.upper() for s in getattr(self._settings, "filtered_wand_ids", [])])
            self._logger.debug(
                f"WandServer started. header_ttl_s={float(self._settings.header_ttl_s):.3f} "
                f"disconnect_after_s={float(self._settings.disconnect_after_s):.3f} "
                f"filter_wands={bool(self._settings.filter_wands)} "
                f"filtered_ids={filtered_ids}"
            )

    async def stop(self) -> None:
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Stopping wand server...")

        self._serial.data_received.unsubscribe(self._on_line)
        await self._serial.stop()

        self._pending_headers.clear()

        # Clean up clients
        for client in list(self._connected_clients.values()):
            client.wand_rotation_raw_updated.unsubscribe(self._on_wand_rotation_raw_updated)
        self._connected_clients.clear()

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("WandServer stopped.")

    def update(self) -> None:
        now = time.monotonic()
        self._prune_pending_headers(now)
        self._prune_disconnected_clients(now)
        self._maybe_log_stats(now)

    # ── public helpers ───────────────────────────────────────────────────────

    def connected_clients(self) -> list[WandClient]:
        """Snapshot of currently connected clients (do not mutate)."""
        return list(self._connected_clients.values())

    # ── internal ─────────────────────────────────────────────────────────────

    def _maybe_log_stats(self, now: float) -> None:
        if not self._logger.isEnabledFor(logging.DEBUG):
            return
        if (now - self._last_stats_log_monotonic) < self._stats_log_interval_s:
            return

        self._last_stats_log_monotonic = now
        self._logger.debug(
            f"WandServer stats: lines={self._lines_total} pkt={self._lines_pkt} data={self._lines_data} "
            f"orphan_data={self._lines_orphan_data} unparsed={self._lines_unparsed} empty={self._lines_empty} "
            f"pending_headers={len(self._pending_headers)} clients={len(self._connected_clients)} "
            f"filtered={self._lines_filtered}"
        )

    def _prune_pending_headers(self, now: float) -> None:
        if not self._pending_headers:
            return

        ttl = float(self._settings.header_ttl_s)
        expired = [seq for seq, (_, _, _, t0) in self._pending_headers.items() if (now - t0) > ttl]
        if not expired:
            return

        for seq in expired:
            self._pending_headers.pop(seq, None)

        if self._logger.isEnabledFor(logging.DEBUG):
            preview = expired[:10]
            suffix = "…" if len(expired) > 10 else ""
            self._logger.debug(
                f"Pruned {len(expired)} expired PKT headers. ttl_s={ttl:.3f} seq_preview={preview}{suffix} "
                f"pending_now={len(self._pending_headers)}"
            )

    def _get_or_create_client(self, client_id: str) -> WandClient | None:
        client_id = client_id.upper()

        client = self._connected_clients.get(client_id)
        if client is not None:
            return client

        if self._settings.filter_wands and client_id not in self._settings.filtered_wand_ids:
            self._lines_filtered += 1
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(f"Ignoring wand {client_id}. filter_wands=True and id not in filtered_wand_ids.")
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
            self._lines_empty += 1
            return

        self._lines_total += 1

        line = line.strip()  # IMPORTANT: handles CRLF (\r\n) from serial
        if not line:
            self._lines_empty += 1
            return

        now = time.monotonic()

        # PKT header
        m = self._PKT_RE.match(line)
        if m:
            self._lines_pkt += 1

            seq = int(m["seq"])
            t_base = int(m["t_base"])
            tag_hex = m["tag"].upper()
            nsamp = int(m["nsamp"])

            if seq in self._pending_headers and self._logger.isEnabledFor(logging.DEBUG):
                old_t_base, old_tag, old_nsamp, old_t0 = self._pending_headers[seq]
                self._logger.debug(
                    f"PKT seq overwrite: seq={seq} "
                    f"old=(t_base={old_t_base} tag={old_tag} nsamp={old_nsamp} age_s={(now - old_t0):.3f}) "
                    f"new=(t_base={t_base} tag={tag_hex} nsamp={nsamp})"
                )

            self._pending_headers[seq] = (t_base, tag_hex, nsamp, now)

            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(
                    f"PKT: seq={seq} tag={tag_hex} t_base={t_base} nsamp={nsamp} pending_headers={len(self._pending_headers)}"
                )
            return

        if line.startswith("PKT") and self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(f"PKT format mismatch (regex failed). line='{line}'")

        # DATA batch
        m = self._DATA_RE.match(line)
        if not m:
            self._lines_unparsed += 1
            if self._logger.isEnabledFor(logging.DEBUG):
                preview = line if len(line) <= 200 else f"{line[:200]}…"
                self._logger.debug(f"Unparsed serial line. preview='{preview}'")
            return

        self._lines_data += 1

        seq = int(m["seq"])
        data_str = m["data"].strip()

        # strip optional quotes (DATA can be quoted or not)
        if len(data_str) >= 2 and data_str[0] == '"' and data_str[-1] == '"':
            data_str = data_str[1:-1]

        header = self._pending_headers.pop(seq, None)
        if header is None:
            self._lines_orphan_data += 1
            if self._logger.isEnabledFor(logging.DEBUG):
                preview = data_str if len(data_str) <= 140 else f"{data_str[:140]}…"
                self._logger.debug(
                    f"DATA orphan (no PKT header): seq={seq} data_len={len(data_str)} "
                    f"data_preview='{preview}' pending_headers={len(self._pending_headers)}"
                )
            return  # no header => can't route DATA to a tag/t_base

        t_base, tag_hex, nsamp, t0 = header

        if self._logger.isEnabledFor(logging.DEBUG):
            age_s = now - t0
            preview = data_str if len(data_str) <= 140 else f"{data_str[:140]}…"
            self._logger.debug(
                f"DATA: seq={seq} tag={tag_hex} t_base={t_base} nsamp={nsamp} hdr_age_s={age_s:.3f} "
                f"data_len={len(data_str)} data_preview='{preview}'"
            )

        client = self._get_or_create_client(tag_hex)
        if client is None:
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(f"DATA dropped (client filtered): tag={tag_hex} seq={seq}")
            return

        try:
            client.on_wand_rotation_data(t_base, data_str)
        except Exception:
            self._logger.exception(f"Exception while routing wand data: tag={tag_hex} seq={seq} t_base={t_base} data_len={len(data_str)}")

    def _on_wand_rotation_raw_updated(self, msg: WandRotationRaw) -> None:
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(
                f"wand_rotation_raw_updated: id={getattr(msg, 'id', '?')} "
                f"ts={getattr(msg, 'ms', -1)} "
                f"yaw={getattr(msg, 'yaw', float('nan')):.3f} "
                f"pitch={getattr(msg, 'pitch', float('nan')):.3f}"
            )
        self.wand_rotation_raw_updated.invoke(msg)
