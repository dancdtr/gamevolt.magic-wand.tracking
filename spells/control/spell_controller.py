# spells/control/udp_spell_controller.py
from __future__ import annotations

from logging import Logger

from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from gamevolt.messaging.udp.configuration.udp_peer_settings import UdpPeerSettings
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.hello_message import HelloMessage
from messaging.target_spell_updated_message import TargetSpellUpdatedMessage
from spells.control.spell_target_store import SpellTargetStore
from spells.spell import Spell
from spells.spell_list import SpellList


class SpellController:
    def __init__(self, logger: Logger, settings: UdpPeerSettings, spell_list: SpellList) -> None:
        self._logger = logger
        self._spell_list = spell_list
        self._store = SpellTargetStore(logger, spell_list)

        self._udp_transmitter = UdpTx(logger, settings.udp_transmitter)
        self._udp_message_handler = MessageHandler(logger, UdpRx(logger, settings.udp_receiver))

    @property
    def target_spell(self) -> Spell:
        return self._store.target_spell

    @property
    def target_spell_updated(self) -> Event:
        return self._store.target_spell_updated

    def start(self) -> None:
        self._logger.debug("Starting UdpSpellController")
        self._udp_message_handler.subscribe(TargetSpellUpdatedMessage, self._on_target_spell_updated)
        self._udp_message_handler.start()

        self._udp_transmitter.send(HelloMessage().to_dict())

    def stop(self) -> None:
        self._logger.debug("Stopping UdpSpellController")
        self._udp_message_handler.unsubscribe(TargetSpellUpdatedMessage, self._on_target_spell_updated)
        self._udp_message_handler.stop()

    def _on_target_spell_updated(self, message: Message) -> None:
        self._logger.debug(f"Received UDP message: {message!r}")

        if not isinstance(message, TargetSpellUpdatedMessage):
            return

        spell = self._spell_list.get_by_name(message.SpellTypeName.casefold())
        self._logger.info(f"Setting spell target to: {spell.long_name}")
        self._store.set_target_by_type(spell.type)
