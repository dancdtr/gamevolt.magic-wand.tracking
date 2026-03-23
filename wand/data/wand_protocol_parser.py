import re

from wand.data.data_line import DataLine
from wand.packet_header import PacketHeader


class WandProtocolParser:
    _PKT_RE = re.compile(
        r"^PKT\s+"
        r"t_rx=(?P<t_rx>\d+)\s+"
        r"t0=(?P<t0>\d+)\s+"
        r"dt_us=(?P<dt_us>\d+)\s+"
        r"tag=(?P<tag>[0-9A-Fa-f]+)\s+"
        r"seq=(?P<seq>\d+)\s+"
        r"nsamp=(?P<nsamp>\d+)"
        r"(?:\s+fmt=(?P<fmt>[A-Za-z0-9_]+))?\s*$"
    )

    _DATA_RE = re.compile(r'^(?:DATA|DATA_RAW)\s+seq=(?P<seq>\d+)\s+data="?(?P<data>.*)"?\s*$')

    def parse(self, line: str, now: float) -> PacketHeader | DataLine | None:
        m = self._PKT_RE.match(line)
        if m:
            seq = int(m["seq"])
            t0_ms = int(m["t0"])
            sample_dt_us = int(m["dt_us"])
            tag_hex = m["tag"].upper()
            nsamp = int(m["nsamp"])
            fmt = (m["fmt"] or "yawpitch").lower()

            return PacketHeader(
                seq=seq,
                t0_ms=t0_ms,
                sample_dt_us=sample_dt_us,
                tag_hex=tag_hex,
                nsamp=nsamp,
                fmt=fmt,
                received_monotonic=now,
            )

        m = self._DATA_RE.match(line)
        if m:
            seq = int(m["seq"])
            data_str = m["data"].strip()

            if len(data_str) >= 2 and data_str[0] == '"' and data_str[-1] == '"':
                data_str = data_str[1:-1]

            return DataLine(seq=seq, data_str=data_str)

        return None
