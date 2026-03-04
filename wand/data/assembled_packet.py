from dataclasses import dataclass


@dataclass(frozen=True)
class AssembledPacket:
    seq: int
    t_base_ms: int
    tag_hex: str
    nsamp: int
    data_str: str
    header_age_s: float
