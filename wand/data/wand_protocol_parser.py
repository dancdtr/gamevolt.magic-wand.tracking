import re

from wand.data.data_line import DataLine
from wand.packet_header import PacketHeader


class WandProtocolParser:
    _PKT_RE = re.compile(
        r"^PKT\s+t_rx=(?P<t_rx>\d+)\s+t_base=(?P<t_base>\d+)\s+tag=(?P<tag>[0-9A-Fa-f]+)\s+seq=(?P<seq>\d+)\s+nsamp=(?P<nsamp>\d+)\s*$"
    )
    _DATA_RE = re.compile(r'^(?:DATA|DATA_RAW)\s+seq=(?P<seq>\d+)\s+data="?(?P<data>.*)"?\s*$')

    def parse(self, line: str, now: float) -> PacketHeader | DataLine | None:
        """
        Returns:
          - PktHeader if line is a PKT header
          - DataLine if line is a DATA batch
          - None if unparsed
        """
        m = self._PKT_RE.match(line)
        if m:
            seq = int(m["seq"])
            t_base = int(m["t_base"])
            tag_hex = m["tag"].upper()
            nsamp = int(m["nsamp"])
            return PacketHeader(seq=seq, t_base_ms=t_base, tag_hex=tag_hex, nsamp=nsamp, received_monotonic=now)

        m = self._DATA_RE.match(line)
        if m:
            seq = int(m["seq"])
            data_str = m["data"].strip()

            # strip optional quotes (DATA can be quoted or not)
            if len(data_str) >= 2 and data_str[0] == '"' and data_str[-1] == '"':
                data_str = data_str[1:-1]

            return DataLine(seq=seq, data_str=data_str)

        return None
