from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from gamevolt.logging._levels import register_custom_levels
from gamevolt.logging._logger import Logger
from wand.streaming.eliko.wand_battery_log import WandBatteryLog


def _logger() -> Logger:
    register_custom_levels()
    logging.setLoggerClass(Logger)
    log = logging.getLogger("test.wand_battery_log")
    log.setLevel(logging.WARNING)
    return log  # type: ignore[return-value]


def test_creates_daily_file_with_header_and_appends(tmp_path: Path) -> None:
    log = WandBatteryLog(logger=_logger(), output_dir=tmp_path / "battery")

    log.record("1DAD", 1522, 84.4)
    log.record("1DAD", 1510, 82.0)

    path = tmp_path / "battery" / f"battery_{datetime.now():%Y%m%d}.csv"
    lines = path.read_text().splitlines()

    assert lines[0] == "timestamp,tag,millivolts,percent"
    assert len(lines) == 3
    assert lines[1].endswith(",1DAD,1522,84.4")
    assert lines[2].endswith(",1DAD,1510,82.0")
    # Timestamp column parses back as ISO.
    datetime.fromisoformat(lines[1].split(",")[0])
