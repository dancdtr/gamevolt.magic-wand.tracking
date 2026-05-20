from __future__ import annotations

from abc import ABC, abstractmethod


class WandPresenceReporterBase(ABC):
    @abstractmethod
    async def report_detected(self, wand_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def report_entered(self, wand_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def report_exit(self, wand_id: str) -> None:
        raise NotImplementedError()
