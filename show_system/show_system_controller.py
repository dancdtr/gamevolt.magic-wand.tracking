from logging import Logger

from gamevolt.messaging.udp.udp_tx import UdpTx
from show_system.configuration.show_system_controller_settings import ShowSystemControllerSettings
from spells.spell_type import SpellType
from wizards.wizard_level_type import WizardLevelType


class ShowSystemController:
    def __init__(self, logger: Logger, settings: ShowSystemControllerSettings, show_system_tx: UdpTx, lamp_tx: UdpTx) -> None:
        self._show_system_tx = show_system_tx
        self._settings = settings
        self._lamp_tx = lamp_tx
        self._logger = logger

    def play_spell(self, spell_type: SpellType, level: WizardLevelType) -> None:
        if spell_type in (SpellType.LUMOS_MAXIMA, SpellType.NOX):
            self._logger.info(f"Notifying lamp to show '{spell_type.name}' for level '{level.name}'...")
            self._lamp_tx.send_str(spell_type.name.capitalize())
            return

        else:
            message = {
                "SpellCast": f"{spell_type.name.upper()}",
                "Level": f"{level.name.upper()}",
            }
            self._logger.info(f"Notifying show system to play '{spell_type.name}' for level '{level.name}'...")
            self._show_system_tx.send(message)
