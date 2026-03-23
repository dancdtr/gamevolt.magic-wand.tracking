from __future__ import annotations

import time
from dataclasses import dataclass
from logging import Logger

from anchor_area.anchor_area import AnchorArea
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from gamevolt.web_sockets.web_socket_client import WebSocketClient
from wand.data.data_line import DataLine
from wand.data.wand_protocol_parser import WandProtocolParser
from wand.packet_header import PacketHeader


@dataclass
class PendingRelayPacket:
    header: PacketHeader
    raw_header_line: str


class AnchorRelay:
    def __init__(
        self,
        logger: Logger,
        line_receiver_protocol: LineReceiverProtocol,
        web_socket_client: WebSocketClient,
        anchor_area: AnchorArea,
        header_ttl_s: float = 2.0,
    ) -> None:
        self._line_receiver_protocol = line_receiver_protocol
        self._web_socket_client = web_socket_client
        self._zone_prescence = anchor_area
        self._logger = logger

        self._parser = WandProtocolParser()
        self._header_ttl_s = float(header_ttl_s)
        self._pending: dict[int, PendingRelayPacket] = {}

    async def start_async(self) -> None:
        self._line_receiver_protocol.line_received.subscribe(self._on_line_received)

        await self._line_receiver_protocol.start()

    async def stop_async(self) -> None:
        await self._line_receiver_protocol.stop()

        self._line_receiver_protocol.line_received.unsubscribe(self._on_line_received)
        self._pending.clear()

    def update(self) -> None:
        now = time.monotonic()
        expired = [seq for seq, pending in self._pending.items() if (now - pending.header.received_monotonic) > self._header_ttl_s]
        for seq in expired:
            self._pending.pop(seq, None)

    def _on_line_received(self, raw: str) -> None:
        raw = raw.strip()
        if not raw:
            return

        now = time.monotonic()
        parsed = self._parser.parse(raw, now)

        if parsed is None:
            return

        if isinstance(parsed, PacketHeader):
            self._on_header(raw, parsed)
            return

        if isinstance(parsed, DataLine):
            self._on_data(raw, parsed)
            return

    def _on_header(self, raw: str, header: PacketHeader) -> None:
        if not self._zone_prescence.is_present(header.tag_hex):
            self._logger.debug(f"Dropping PKT for non-present wand: tag={header.tag_hex} seq={header.seq}")
            return

        self._pending[header.seq] = PendingRelayPacket(
            header=header,
            raw_header_line=raw,
        )

    def _on_data(self, raw: str, data: DataLine) -> None:
        pending = self._pending.pop(data.seq, None)
        if pending is None:
            return

        self._web_socket_client.send_data(pending.raw_header_line)
        self._web_socket_client.send_data(raw)
