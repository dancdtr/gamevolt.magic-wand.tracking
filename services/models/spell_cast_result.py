from __future__ import annotations

from dataclasses import dataclass

from spells.spell_cast_quality import SpellCastQuality


@dataclass(frozen=True)
class SpellCastResult:
    wand_id: str
    spell_name: str
    quality: SpellCastQuality
