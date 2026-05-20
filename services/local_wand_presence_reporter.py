from __future__ import annotations

from gamevolt.logging._logger import Logger
from services.wand_presence_reporter_base import WandPresenceReporterBase


class LocalWandPresenceReporter(WandPresenceReporterBase):
    """Log-only stand-in. Real impl will POST to the hub."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def report_detected(self, wand_id: str) -> None:
        self._logger.info(f"LocalWandPresenceReporter detected ({wand_id})")

    async def report_entered(self, wand_id: str) -> None:
        self._logger.info(f"LocalWandPresenceReporter entered ({wand_id})")

    async def report_exit(self, wand_id: str) -> None:
        self._logger.info(f"LocalWandPresenceReporter exit ({wand_id})")
