from dataclasses import dataclass


@dataclass(frozen=True)
class AssembledPacket:
    seq: int
    t0_ms: int
    sample_dt_us: int
    tag_hex: str
    nsamp: int
    fmt: str
    data_str: str
    header_age_s: float
