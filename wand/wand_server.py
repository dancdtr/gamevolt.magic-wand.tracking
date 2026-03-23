from __future__ import annotations

import logging
import time
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from wand.configuration.wand_server_settings import WandServerSettings
from wand.data.data_line import DataLine
from wand.data.wand_protocol_parser import WandProtocolParser
from wand.packet_data_assembler import PktDataAssembler
from wand.packet_header import PacketHeader
from wand.wand_client import WandClient
from wand.wand_client_registry import WandClientRegistry
from wand.wand_id_filter import WandIdFilter
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server_protocol import WandServerProtocol
from wand.wand_server_stats import WandServerStats


class WandServer(WandServerProtocol):
    def __init__(self, logger: Logger, settings: WandServerSettings, line_receiver: LineReceiverProtocol) -> None:
        self._wand_rotation_raw_updated: Event[Callable[[WandRotationRaw], None]] = Event()
        self._wand_disconnected: Event[Callable[[WandClient], None]] = Event()
        self._wand_connected: Event[Callable[[WandClient], None]] = Event()

        self._line_receiver = line_receiver
        self._settings = settings
        self._logger = logger

        self._parser = WandProtocolParser()
        self._assembler = PktDataAssembler(logger=logger, header_ttl_s=float(settings.header_ttl_s))
        self._filter = WandIdFilter(settings=settings)

        self._registry = WandClientRegistry(
            logger=logger,
            settings=settings,
            wand_filter=self._filter,
            on_connected=self._wand_connected.invoke,
            on_disconnected=self._wand_disconnected.invoke,
            on_rotation_raw=self._on_wand_rotation_raw_updated,
        )

        self._stats = WandServerStats(last_log_monotonic=time.monotonic(), log_interval_s=2.0)

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
        self._line_receiver.line_received.subscribe(self._on_line)
        # await self._line_receiver.start_async()
        self._logger.info(f"Started wand server. Allow list: {self._filter.snapshot()}")

    def stop(self) -> None:
        self._logger.info("Stopping wand server...")
        self._line_receiver.line_received.unsubscribe(self._on_line)
        # await self._line_receiver.stop_async()

        self._registry.clear()
        self._logger.info("WandServer stopped.")

    def update(self) -> None:
        now = time.monotonic()

        expired = self._assembler.prune(now)
        if expired and self._logger.isEnabledFor(logging.DEBUG):
            preview = expired[:10]
            suffix = "…" if len(expired) > 10 else ""
            self._logger.trace(
                f"Pruned {len(expired)} expired PKT headers. ttl_s={float(self._settings.header_ttl_s):.3f} "
                f"seq_preview={preview}{suffix} pending_now={self._assembler.pending_count}"
            )

        self._registry.prune_disconnected(now)
        self._stats.maybe_log(
            logger=self._logger,
            now=now,
            pending_headers=self._assembler.pending_count,
            clients=len(self._registry.snapshot()),
        )

    def add_wand_id(self, id: str) -> None:
        self._filter.add(id)

    def remove_wand_id(self, id: str) -> None:
        self._filter.remove(id)

    def connected_clients(self) -> list[WandClient]:
        return self._registry.snapshot()

    def _on_line(self, line: str) -> None:
        if not line:
            self._stats.lines_empty += 1
            return

        self._stats.lines_total += 1

        line = line.strip()
        if not line:
            self._stats.lines_empty += 1
            return

        now = time.monotonic()
        parsed = self._parser.parse(line, now)

        if isinstance(parsed, PacketHeader):
            self._stats.lines_pkt += 1
            self._assembler.on_header(parsed)
            return

        if parsed is None:
            self._stats.lines_unparsed += 1
            if line.startswith("PKT"):
                self._logger.debug(f"PKT format mismatch (regex failed). line='{line}'")
            else:
                preview = line if len(line) <= 200 else f"{line[:200]}…"
                self._logger.debug(f"Unparsed serial line. preview='{preview}'")
            return

        assert isinstance(parsed, DataLine)
        self._stats.lines_data += 1

        pkt = self._assembler.on_data(parsed, now)
        if pkt is None:
            self._stats.lines_orphan_data += 1
            preview = parsed.data_str if len(parsed.data_str) <= 140 else f"{parsed.data_str[:140]}…"
            self._logger.debug(
                f"DATA orphan (no PKT header): seq={parsed.seq} data_len={len(parsed.data_str)} "
                f"data_preview='{preview}' pending_headers={self._assembler.pending_count}"
            )
            return

        preview = pkt.data_str if len(pkt.data_str) <= 140 else f"{pkt.data_str[:140]}…"
        self._logger.trace(
            f"DATA: seq={pkt.seq} tag={pkt.tag_hex} t0={pkt.t0_ms} dt_us={pkt.sample_dt_us} "
            f"nsamp={pkt.nsamp} fmt={pkt.fmt} hdr_age_s={pkt.header_age_s:.3f} "
            f"data_len={len(pkt.data_str)} data_preview='{preview}'"
        )

        client = self._registry.get_or_create(pkt.tag_hex)
        if client is None:
            self._stats.lines_filtered += 1
            self._logger.debug(f"DATA dropped (client filtered): tag={pkt.tag_hex} seq={pkt.seq}")
            return

        try:
            client.on_wand_rotation_data(pkt.t0_ms, pkt.sample_dt_us, pkt.data_str)
        except Exception:
            self._logger.exception(
                f"Exception while routing wand data: tag={pkt.tag_hex} seq={pkt.seq} "
                f"t0={pkt.t0_ms} dt_us={pkt.sample_dt_us} fmt={pkt.fmt} data_len={len(pkt.data_str)}"
            )

    def _on_wand_rotation_raw_updated(self, msg: WandRotationRaw) -> None:
        self._logger.trace(f"wand_rotation_raw_updated: id={msg.id} ts={msg.ms} " f"fx={msg.fx:.4f} fy={msg.fy:.4f} fz={msg.fz:.4f}")
        self.wand_rotation_raw_updated.invoke(msg)
