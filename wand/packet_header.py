# ──────────────────────────────────────────────────────────────────────────────
# Wire model
# ──────────────────────────────────────────────────────────────────────────────


from dataclasses import dataclass


@dataclass(frozen=True)
class PacketHeader:
    seq: int
    t_base_ms: int
    tag_hex: str
    nsamp: int
    received_monotonic: float
