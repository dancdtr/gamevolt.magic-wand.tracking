"""Player XP source: how many distinct spells a player has cast.

This is conceptually hub-side data (per-wizard history, spec 5.1). The protocol lets the
scorer stay agnostic; the in-memory impl is a dev stand-in keyed by wand id for now (should
become wizard id once the session binding is wired through).
"""

from __future__ import annotations

from typing import Protocol


class XpProvider(Protocol):
    def unique_spell_count(self, player_id: str) -> int: ...

    def record_cast(self, player_id: str, spell_label: str) -> None: ...


class InMemoryXpProvider:
    def __init__(self) -> None:
        self._cast: dict[str, set[str]] = {}

    def unique_spell_count(self, player_id: str) -> int:
        return len(self._cast.get(player_id, ()))

    def record_cast(self, player_id: str, spell_label: str) -> None:
        self._cast.setdefault(player_id, set()).add(spell_label)
