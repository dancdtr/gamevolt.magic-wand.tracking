from __future__ import annotations

import logging
import time
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from wand.data.assembled_packet import AssembledPacket
from wand.data.data_line import DataLine
from wand.data.wand_protocol_parser import WandProtocolParser
from wand.packet_data_assembler import PktDataAssembler
from wand.packet_header import PacketHeader


class LineBasedWandSensorStream:
    """Sensor stream backed by a LineReceiverProtocol. Parses wire lines and
    assembles header+data pairs into AssembledPacket frames."""

    def __init__(
        self,
        logger: Logger,
        line_receiver: LineReceiverProtocol,
        header_ttl_s: float,
    ) -> None:
        self._packet_received: Event[Callable[[AssembledPacket], None]] = Event()

        self._logger = logger
        self._line_receiver = line_receiver
        self._header_ttl_s = float(header_ttl_s)

        self._parser = WandProtocolParser()
        self._assembler = PktDataAssembler(logger=logger, header_ttl_s=self._header_ttl_s)

    @property
    def packet_received(self) -> Event[Callable[[AssembledPacket], None]]:
        return self._packet_received

    async def start_async(self) -> None:
        self._line_receiver.line_received.subscribe(self._on_line)
        await self._line_receiver.start()

    async def stop_async(self) -> None:
        await self._line_receiver.stop()
        self._line_receiver.line_received.unsubscribe(self._on_line)

    def update(self) -> None:
        now = time.monotonic()
        expired = self._assembler.prune(now)
        if expired and self._logger.isEnabledFor(logging.DEBUG):
            preview = expired[:10]
            suffix = "…" if len(expired) > 10 else ""
            self._logger.trace(
                f"Pruned {len(expired)} expired PKT headers. ttl_s={self._header_ttl_s:.3f} "
                f"seq_preview={preview}{suffix} pending_now={self._assembler.pending_count}"
            )

    def _on_line(self, line: str) -> None:
        if not line:
            return

        line = line.strip()
        if not line:
            return

        now = time.monotonic()
        parsed = self._parser.parse(line, now)

        if isinstance(parsed, PacketHeader):
            self._assembler.on_header(parsed)
            return

        if parsed is None:
            if line.startswith("PKT"):
                self._logger.debug(f"PKT format mismatch (regex failed). line='{line}'")
            else:
                preview = line if len(line) <= 200 else f"{line[:200]}…"
                self._logger.debug(f"Unparsed serial line. preview='{preview}'")
            return

        assert isinstance(parsed, DataLine)

        packet = self._assembler.on_data(parsed, now)
        if packet is None:
            preview = parsed.data_str if len(parsed.data_str) <= 140 else f"{parsed.data_str[:140]}…"
            self._logger.debug(
                f"DATA orphan (no PKT header): seq={parsed.seq} data_len={len(parsed.data_str)} "
                f"data_preview='{preview}' pending_headers={self._assembler.pending_count}"
            )
            return

        self._packet_received.invoke(packet)
