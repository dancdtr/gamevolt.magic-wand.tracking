import logging
from logging import Logger

from wand.data.assembled_packet import AssembledPacket
from wand.data.data_line import DataLine
from wand.packet_header import PacketHeader


class PktDataAssembler:
    """
    Stores PKT headers by seq, then pops them when DATA arrives.
    Prunes stale headers by TTL.
    """

    def __init__(self, logger: Logger, header_ttl_s: float) -> None:
        self._logger = logger
        self._header_ttl_s = float(header_ttl_s)
        self._pending: dict[int, PacketHeader] = {}

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def on_header(self, header: PacketHeader) -> None:
        if header.seq in self._pending:
            old = self._pending[header.seq]
            self._logger.debug(
                f"PKT seq overwrite: seq={header.seq} "
                f"old=(t_base={old.t_base_ms} tag={old.tag_hex} nsamp={old.nsamp} age_s={(header.received_monotonic - old.received_monotonic):.3f}) "
                f"new=(t_base={header.t_base_ms} tag={header.tag_hex} nsamp={header.nsamp})"
            )
        self._pending[header.seq] = header

        self._logger.debug(
            f"PKT: seq={header.seq} tag={header.tag_hex} t_base={header.t_base_ms} nsamp={header.nsamp} pending_headers={len(self._pending)}"
        )

    def on_data(self, data: DataLine, now: float) -> AssembledPacket | None:
        header = self._pending.pop(data.seq, None)
        if header is None:
            return None

        age_s = now - header.received_monotonic
        return AssembledPacket(
            seq=data.seq,
            t_base_ms=header.t_base_ms,
            tag_hex=header.tag_hex,
            nsamp=header.nsamp,
            data_str=data.data_str,
            header_age_s=age_s,
        )

    def prune(self, now: float) -> list[int]:
        if not self._pending:
            return []

        ttl = self._header_ttl_s
        expired = [seq for seq, hdr in self._pending.items() if (now - hdr.received_monotonic) > ttl]
        for seq in expired:
            self._pending.pop(seq, None)
        return expired
