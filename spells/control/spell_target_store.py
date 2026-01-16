# spells/control/spell_target_store.py
from __future__ import annotations

from bisect import bisect_left
from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from spells.spell import Spell
from spells.spell_list import SpellList
from spells.spell_type import SpellType


class SpellTargetStore:
    def __init__(self, logger: Logger, spell_list: SpellList) -> None:
        self._logger = logger
        self._spell_list = spell_list

        self._spells: list[Spell] = sorted(self._spell_list.items, key=lambda s: s.id)

        self._by_id: dict[int, Spell] = {s.id: s for s in self._spells}
        self._by_type: dict[SpellType, Spell] = {s.type: s for s in self._spells}
        self._ids_sorted: list[int] = sorted(self._by_id.keys())
        self._id_to_index: dict[int, int] = {s.id: i for i, s in enumerate(self._spells)}

        default = self._spell_list.get_default()
        if default.id not in self._by_id and self._spells:
            self._logger.warning(f"Default spell {default} not in list; falling back to first spell")
            default = self._spells[0]

        self._target_spell: Spell = default
        self._current_index: int = self._id_to_index.get(self._target_spell.id, 0)

        self.target_spell_updated: Event[Callable[[Spell], None]] = Event()

    @property
    def spells(self) -> list[Spell]:
        return self._spells

    @property
    def target_spell(self) -> Spell:
        return self._target_spell

    @property
    def current_index(self) -> int:
        return self._current_index

    def set_target_by_id(self, spell_id: int) -> None:
        if not self._spells:
            return

        min_id = self._ids_sorted[0]
        max_id = self._ids_sorted[-1]
        clamped_id = max(min_id, min(spell_id, max_id))
        if clamped_id != spell_id:
            self._logger.debug(f"Clamped spell id {spell_id} to {clamped_id}")

        if clamped_id not in self._by_id:
            idx = bisect_left(self._ids_sorted, clamped_id)
            if idx >= len(self._ids_sorted):
                idx = len(self._ids_sorted) - 1
            resolved_id = self._ids_sorted[idx]
        else:
            resolved_id = clamped_id

        self._set_target(self._by_id[resolved_id])

    def set_target_by_type(self, spell_type: SpellType) -> None:
        spell = self._by_type.get(spell_type)
        if spell is None:
            self._logger.warning(f"Unknown spell type: {spell_type}")
            return
        self._set_target(spell)

    def cycle_target(self, delta: int) -> None:
        if not self._spells:
            return

        new_index = max(0, min(self._current_index + delta, len(self._spells) - 1))
        if new_index == self._current_index:
            return

        self._set_target(self._spells[new_index])

    def _set_target(self, spell: Spell) -> None:
        if spell.id == self._target_spell.id:
            return

        self._current_index = self._id_to_index.get(spell.id, 0)
        self._target_spell = spell
        self.target_spell_updated.invoke(self._target_spell)
