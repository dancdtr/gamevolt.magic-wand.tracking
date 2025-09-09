from abc import ABC
from collections.abc import Callable
from logging import Logger

from classification.classifiers.spells.spell import Spell
from gamevolt.events.event import Event


class SpellProviderBase(ABC):
    def __init__(self, logger: Logger) -> None:
        super().__init__()
        self._logger = logger

    @property
    def target_spells(self) -> list[Spell]: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    @property
    def target_spells_updated(self) -> Event[Callable[[list[Spell]], None]]: ...
