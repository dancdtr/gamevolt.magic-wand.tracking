from __future__ import annotations

from datetime import datetime
from pathlib import Path

from gamevolt.logging import Logger


class WandBatteryLog:
    """Append battery readings to a daily CSV for offline plotting.

    One file per day (`battery_YYYYMMDD.csv`), one row per reading:
    ISO timestamp, tag, millivolts, percent. Subscribed to
    `WandBatteryMonitor.battery_updated` by the builder.
    """

    _HEADER = "timestamp,tag,millivolts,percent\n"

    def __init__(self, logger: Logger, output_dir: Path | str) -> None:
        self._logger = logger
        self._output_dir = Path(output_dir)

    def record(self, tag: str, millivolts: int, percent: float) -> None:
        now = datetime.now()
        path = self._output_dir / f"battery_{now:%Y%m%d}.csv"
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            is_new = not path.exists()
            with path.open("a", encoding="utf-8") as f:
                if is_new:
                    f.write(self._HEADER)
                f.write(f"{now.isoformat(timespec='milliseconds')},{tag},{millivolts},{percent:.1f}\n")
        except OSError as e:
            self._logger.warning(f"Failed to append battery reading to {path}: {e}")
