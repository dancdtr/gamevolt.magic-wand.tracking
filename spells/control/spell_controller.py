from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from spells.spell import Spell
from spells.spell_list import SpellList
from spells.spell_type import SpellType


class SpellController:
    def __init__(self, logger: Logger, spell_list: SpellList) -> None:
        self._logger = logger
        self._spell_list = spell_list

        self._spells: list[Spell] = self._spell_list.items
        self._spells.sort(key=lambda s: s.id)

        self._by_id = {s.id: s for s in self._spells}
        self._by_type = {s.type: s for s in self._spells}

        self._target_spell: Spell = self._spell_list.get_default()
        self._current_index = 0

        self._target_spell_updated: Event[Callable[[Spell], None]] = Event()
        self._toggle_history: Event[Callable[[], None]] = Event()
        self._quit: Event[Callable[[], None]] = Event()

    @property
    def spells(self) -> list[Spell]:
        return self._spells

    @property
    def target_spell(self) -> Spell:
        return self._target_spell

    @property
    def target_spell_updated(self) -> Event[Callable[[Spell], None]]:
        return self._target_spell_updated

    @property
    def toggle_history(self) -> Event[Callable[[], None]]:
        return self._toggle_history

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def set_target_by_id(self, spell_id: int) -> None:
        if not self._spells:
            return

        min_id = min(self._by_id.keys())
        max_id = max(self._by_id.keys())
        clamped_id = max(min_id, min(spell_id, max_id))

        if clamped_id != spell_id:
            self._logger.debug(f"Clamped spell id {spell_id} to {clamped_id}")

        spell = self._by_id[clamped_id]
        self._set_target(spell)

    def set_target_by_type(self, spell_type: SpellType) -> None:
        spell = self._by_type.get(spell_type)
        if spell is None:
            self._logger.warning(f"Unknown spell type: {spell_type}")
            return

        self._set_target(spell)

    def cycle_target(self, delta: int) -> None:
        if not self._spells:
            return

        new_index = self._current_index + delta
        new_index = max(0, min(new_index, len(self._spells) - 1))
        if new_index == self._current_index:
            return

        spell = self._spells[new_index]
        self._set_target(spell)

    def _set_target(self, spell: Spell) -> None:
        self._logger.info(f"Setting spell target to: {spell.long_name}")

        try:
            self._current_index = self._spells.index(spell)
        except ValueError:
            self._logger.warning(f"Spell not in spell list: {spell}")
            return

        self._target_spell = spell
        self._target_spell_updated.invoke(self._target_spell)
