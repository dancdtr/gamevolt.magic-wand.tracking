from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from input.wand_position import WandPosition


class MotionInputBase:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self.position_updated: Event[Callable[[WandPosition], None]] = Event()

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    def update(self) -> None: ...

    def reset(self) -> None: ...
