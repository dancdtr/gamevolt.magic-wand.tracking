from __future__ import annotations

from abc import ABC, abstractmethod


class LineSenderProtocol(ABC):
    @abstractmethod
    async def send_line_async(self, line: str) -> None: ...
