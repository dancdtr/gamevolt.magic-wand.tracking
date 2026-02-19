from abc import ABC, abstractmethod
from logging import Logger

from spells.matching.spell_match_context import SpellMatchContext


class SpellRule(ABC):
    def __init__(self, logger: Logger) -> None:
        super().__init__()
        self._logger = logger

    @abstractmethod
    def validate(self, ctx: SpellMatchContext) -> bool: ...

    def __repr__(self) -> str:
        return self.__class__.__name__
