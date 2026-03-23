import logging
from dataclasses import dataclass

from gamevolt.logging import Logger


@dataclass
class WandServerStats:
    lines_total: int = 0
    lines_pkt: int = 0
    lines_data: int = 0
    lines_unparsed: int = 0
    lines_orphan_data: int = 0
    lines_filtered: int = 0
    lines_empty: int = 0

    last_log_monotonic: float = 0.0
    log_interval_s: float = 2.0

    def maybe_log(self, logger: Logger, now: float, pending_headers: int, clients: int) -> None:
        if not logger.isEnabledFor(logging.DEBUG):
            return
        if (now - self.last_log_monotonic) < self.log_interval_s:
            return

        self.last_log_monotonic = now
        logger.trace(
            f"WandServer stats: lines={self.lines_total} pkt={self.lines_pkt} data={self.lines_data} "
            f"orphan_data={self.lines_orphan_data} unparsed={self.lines_unparsed} empty={self.lines_empty} "
            f"pending_headers={pending_headers} clients={clients} filtered={self.lines_filtered}"
        )
