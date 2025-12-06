from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.messaging.udp.configuration.udp_peer_settings import UdpPeerSettings
from spells.selection.spell_selector_base import SpellSelectorBase
from spells.spell import Spell
from spells.spell_factory import SpellFactory
from spells.spell_type import SpellType


class RevelioSpellSelector(SpellSelectorBase):
    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)

        self._spell_factory = SpellFactory()

        self._target_spells: list[Spell] = [self._spell_factory.create(SpellType.REVELIO)]

        self._target_spells_updated = Event[Callable[[list[Spell]], None]]()

    @property
    def target_spells_updated(self) -> Event[Callable[[list[Spell]], None]]:
        return self._target_spells_updated

    @property
    def toggle_history(self) -> Event[Callable[[], None]]: ...

    @property
    def quit(self) -> Event[Callable[[], None]]: ...

    @property
    def target_spells(self) -> list[Spell]:
        return self._target_spells

    def start(self) -> None:
        super().start()
