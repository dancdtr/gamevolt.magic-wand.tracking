from logging import Logger

from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.show_system_spell_cast_message import ShowSystemSpellCastMessage
from show_system.configuration.show_system_controller_settings import ShowSystemControllerSettings
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_type import SpellType
from wizards.hogwarts_house import HogwartsHouse


class ShowSystemController:
    def __init__(self, logger: Logger, settings: ShowSystemControllerSettings, show_system_tx: UdpTx, lamp_tx: UdpTx) -> None:
        self._show_system_tx = show_system_tx
        self._settings = settings
        self._lamp_tx = lamp_tx
        self._logger = logger

    def play_spell(self, spell_type: SpellType, quality: SpellCastQuality, house: HogwartsHouse) -> None:
        message = ShowSystemSpellCastMessage(spell_type, quality, house)

        self._logger.info(f"Notifying show system to play '{spell_type.name}' for quality '{quality.name}', house: '{house.name}'...")
        self._show_system_tx.send(message.to_dict())
