from logging import Logger

from gamevolt.messaging.udp.udp_tx import UdpTx
from show_system.configuration.show_system_controller_settings import ShowSystemControllerSettings
from show_system.wizard_level import WizardLevel
from spells.spell_type import SpellType


class ShowSystemController:
    def __init__(self, logger: Logger, settings: ShowSystemControllerSettings, udp_tx: UdpTx) -> None:
        self._show_system_settings = settings
        self._logger = logger
        self._udp_tx = udp_tx

    def play_spell(self, spell_type: SpellType, level: WizardLevel) -> None:
        message = {
            "SpellCast": f"{spell_type.name.upper()}",
            "Level": f"{level.name.upper()}",
        }

        self._logger.info(f"Notifying show system to play '{spell_type.name}' for level '{level.name}'...")
        self._udp_tx.send(message)
