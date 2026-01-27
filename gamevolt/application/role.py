from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Awaitable


class Role(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def entry_point(self) -> Awaitable[int | None]:
        """Return the awaitable to run (do imports inside this)."""
        raise NotImplementedError

    async def run(self) -> int:
        try:
            rc = await self.entry_point()
            return int(rc or 0)
        except asyncio.CancelledError:
            return 0
        except KeyboardInterrupt:
            return 0
