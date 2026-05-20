from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpellCastResult:
    wand_id: str
    spell_name: str
    success: bool
