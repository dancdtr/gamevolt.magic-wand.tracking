from dataclasses import dataclass


@dataclass(frozen=True)
class PacketHeader:
    seq: int
    tag_hex: str
    t0_ms: int
    sample_dt_us: int
    nsamp: int
    fmt: str
    received_monotonic: float
