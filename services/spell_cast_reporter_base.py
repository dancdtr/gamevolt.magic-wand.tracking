from __future__ import annotations

from abc import ABC, abstractmethod

from spells.spell_match import SpellMatch


class SpellCastReporterBase(ABC):
    @abstractmethod
    async def report_spell_cast(self, match: SpellMatch) -> None:
        raise NotImplementedError()
