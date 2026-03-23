from gamevolt.logging import Logger
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
            self._logger.trace(
                f"PKT seq overwrite: seq={header.seq} "
                f"old=(t0={old.t0_ms} dt_us={old.sample_dt_us} tag={old.tag_hex} nsamp={old.nsamp} fmt={old.fmt} "
                f"age_s={(header.received_monotonic - old.received_monotonic):.3f}) "
                f"new=(t0={header.t0_ms} dt_us={header.sample_dt_us} tag={header.tag_hex} nsamp={header.nsamp} fmt={header.fmt})"
            )

        self._pending[header.seq] = header

        self._logger.trace(
            f"PKT: seq={header.seq} tag={header.tag_hex} t0={header.t0_ms} dt_us={header.sample_dt_us} "
            f"nsamp={header.nsamp} fmt={header.fmt} pending_headers={len(self._pending)}"
        )

    def on_data(self, data: DataLine, now: float) -> AssembledPacket | None:
        header = self._pending.pop(data.seq, None)
        if header is None:
            return None

        age_s = now - header.received_monotonic
        return AssembledPacket(
            seq=data.seq,
            t0_ms=header.t0_ms,
            sample_dt_us=header.sample_dt_us,
            tag_hex=header.tag_hex,
            nsamp=header.nsamp,
            fmt=header.fmt,
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
