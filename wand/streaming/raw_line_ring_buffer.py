from __future__ import annotations

import threading
from collections import deque
from datetime import datetime
from pathlib import Path

from gamevolt.logging import Logger
from wand.streaming.wand_line_source import WandLineSource


class RawLineRingBuffer:
    """Always-on capture of the most recent raw lines from a WandLineSource.

    Keeps the last `capacity` lines (with wall-clock receive times) in memory so
    a transient glitch can be captured *after* it is seen, without running with
    file logging enabled. `dump()` writes the current buffer to a timestamped
    file and returns its path.

    Appends happen on the transport's receive thread; `dump()` may be called
    from any thread (e.g. a Qt key callback) — the lock keeps the snapshot
    consistent.
    """

    _TIME_FMT = "%H:%M:%S.%f"

    def __init__(
        self,
        logger: Logger,
        line_source: WandLineSource,
        output_dir: Path | str = "./diagnostics",
        capacity: int = 2000,
    ) -> None:
        self._logger = logger
        self._line_source = line_source
        self._output_dir = Path(output_dir)
        self._lines: deque[tuple[datetime, str]] = deque(maxlen=max(1, capacity))
        self._lock = threading.Lock()

    def attach(self) -> None:
        self._line_source.line_received.subscribe(self._on_line)

    def detach(self) -> None:
        self._line_source.line_received.unsubscribe(self._on_line)

    def _on_line(self, line: str) -> None:
        with self._lock:
            self._lines.append((datetime.now(), line))

    def dump(self) -> Path | None:
        """Write the buffered lines to a timestamped file; newest last."""
        with self._lock:
            snapshot = list(self._lines)

        if not snapshot:
            self._logger.info("Raw line dump requested but buffer is empty; nothing written.")
            return None

        self._output_dir.mkdir(parents=True, exist_ok=True)
        path = self._output_dir / f"raw_lines_{datetime.now():%Y%m%d_%H%M%S}.log"
        with path.open("w", encoding="utf-8") as f:
            for received_at, line in snapshot:
                f.write(f"{received_at:{self._TIME_FMT}} {line}\n")

        self._logger.info(f"Dumped {len(snapshot)} raw lines to {path} (span {snapshot[0][0]:{self._TIME_FMT}} → {snapshot[-1][0]:{self._TIME_FMT}}).")
        return path
