from __future__ import annotations

from abc import ABC, abstractmethod

from services.models.spell_cast_result import SpellCastResult
from spells.spell_match import SpellMatch


class SpellCastReporterBase(ABC):
    @abstractmethod
    async def report_spell_cast(self, match: SpellMatch) -> SpellCastResult:
        raise NotImplementedError()
