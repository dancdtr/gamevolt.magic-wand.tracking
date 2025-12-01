from logging import Logger

from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.configuration.unity_udp_tx_settings import UnityUdpTxSettings
from spells.spell_match import SpellMatch
from spells.spell_type import SpellType


class UnityUdpTx:
    def __init__(self, logger: Logger, settings: UnityUdpTxSettings):
        self._logger = logger
        self._settings = settings

        self._udp_tx = UdpTx(logger, settings.udp_tx)

    def on_spell_detected(self, spell: SpellMatch) -> None:
        print(self._settings.spell_mappings)
        spell_command = self._settings.spell_mappings.get(spell.spell_name)

        if spell_command:
            payload = f"{spell_command}"
            self._udp_tx.send_str(payload)
