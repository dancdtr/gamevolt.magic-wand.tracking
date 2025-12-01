from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.messaging.udp.udp_rx import UdpRx
from spells.selection.configuration.spell_selector_settings import SpellSelectorSettings
from spells.selection.spell_selector_base import SpellSelectorBase
from spells.spell import Spell
from spells.spell_factory import SpellFactory
from spells.spell_type import SpellType


class UdpSpellSelector(SpellSelectorBase):
    def __init__(self, logger: Logger, settings: SpellSelectorSettings) -> None:
        super().__init__(logger)

        self._udp_receiver = UdpRx(logger, settings.udp_receiver)
        self._spell_factory = SpellFactory()

        self._target_spells: list[Spell] = [self._spell_factory.create(SpellType.NONE)]

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

        self._udp_receiver.message_received.subscribe(self._on_message_received)
        self._udp_receiver.start()

    def _on_message_received(self, message: str) -> None:
        self._logger.debug(message)

        if "INCENDIO" in message:
            spell_type = SpellType.INCENDIO
        elif "WINGARDIUM_LEVIOSA" in message:
            spell_type = SpellType.WINGARDIUM_LEVIOSA
        elif "ALOHOMORA" in message:
            spell_type = SpellType.ALOHOMORA
        else:
            spell_type = SpellType.NONE

        spell = self._spell_factory.create(spell_type)
        self._target_spells = [spell]

        self._logger.info(f"Settings target spells to: {[spell.name for spell in self._target_spells]}")
        self.target_spells_updated.invoke(self._target_spells)
