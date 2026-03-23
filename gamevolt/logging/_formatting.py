from __future__ import annotations

from datetime import datetime
from logging import Formatter, LogRecord
from typing import Optional

from ._levels import level_to_name_map


class GameVoltFormatter(Formatter):
    def __init__(self) -> None:
        super().__init__(fmt="%(asctime)s [%(levelname)s] (%(module)s) %(message)s")

    def format(self, record: LogRecord) -> str:
        original_levelname = record.levelname
        try:
            record.levelname = level_to_name_map.get(record.levelno, original_levelname)
            return super().format(record)
        finally:
            record.levelname = original_levelname

    def formatTime(self, record: LogRecord, datefmt: Optional[str] = None) -> str:
        try:
            creation_time = datetime.utcfromtimestamp(record.created)
            return creation_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        except Exception:
            return super().formatTime(record, datefmt)
