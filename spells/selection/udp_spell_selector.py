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

    @property
    def target_spells_updated(self) -> Event[Callable[[list[Spell]], None]]: ...

    @property
    def toggle_history(self) -> Event[Callable[[], None]]: ...

    @property
    def quit(self) -> Event[Callable[[], None]]: ...

    def start(self) -> None:
        super().start()

        self._udp_receiver.message_received.subscribe(self._on_message_received)
        self._udp_receiver.start()

    def _on_message_received(self, message: str) -> None:
        # handle spell deserialisation

        self._logger.info(message)

        spell_type = SpellType.INCENDIO
        spell = self._spell_factory.create(spell_type)
        self.target_spells_updated.invoke([spell])
