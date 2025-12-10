from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from motion.motion_processor import MotionProcessor
from wand.wand_rotation import WandRotation


class WandBase:
    def __init__(self, logger: Logger, motion_processor: MotionProcessor) -> None:
        self._logger = logger
        self.position_updated: Event[Callable[[WandRotation], None]] = Event()

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    def update(self) -> None: ...

    def reset(self) -> None: ...
