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

    def play_spell(self, wand_id: str, spell_type: SpellType, quality: SpellCastQuality, house: HogwartsHouse) -> None:
        message = ShowSystemSpellCastMessage(
            wand_id=self._format_wand_id(wand_id),
            spell_type=spell_type,
            quality=quality,
            house=house,
        )

        self._logger.info(f"Notifying show system to play '{spell_type.name}' for quality '{quality.name}', house: '{house.name}'...")
        self._show_system_tx.send(message.to_dict())

    @staticmethod
    def _format_wand_id(wand_id: str) -> str:
        """Wand ids are bare upper hex internally; the show system / RTLS wire
        form keeps the `0x` prefix so downstream consumers handle it directly."""
        return wand_id if wand_id.lower().startswith("0x") else f"0x00{wand_id}"
