from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from spells.control.spell_controller import SpellController
from spells.spell import Spell
from spells.spell_list import SpellList
from spells.spell_type import SpellType


class RevelioSpellSelector(SpellController):
    def __init__(self, logger: Logger, spell_list: SpellList) -> None:
        self._logger = logger

        self._spell_list = spell_list

        self._target_spells: list[Spell] = [self._spell_list.get_by_type(SpellType.REVELIO)]

        self._target_spell_updated = Event[Callable[[list[Spell]], None]]()

    @property
    def target_spell_updated(self) -> Event[Callable[[list[Spell]], None]]:
        return self._target_spell_updated

    @property
    def toggle_history(self) -> Event[Callable[[], None]]: ...

    @property
    def quit(self) -> Event[Callable[[], None]]: ...

    @property
    def target_spell(self) -> list[Spell]:
        return self._target_spells

    def start(self) -> None:
        super().start()
