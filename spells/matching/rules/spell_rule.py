from abc import ABC, abstractmethod

from spells.matching.spell_match_context import SpellMatchContext


class SpellRule(ABC):
    """Stateless post-match rule."""

    @abstractmethod
    def validate(self, ctx: SpellMatchContext) -> bool: ...

    def __repr__(self) -> str:
        return self.__class__.__name__
