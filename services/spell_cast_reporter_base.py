from __future__ import annotations

from abc import ABC, abstractmethod

from services.models.spell_cast_result import SpellCastResult
from spells.spell_cast import SpellCast


class SpellCastReporterBase(ABC):
    @abstractmethod
    async def report_spell_cast(self, cast: SpellCast) -> SpellCastResult:
        raise NotImplementedError()
