from logging import Logger

from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.configuration.unity_udp_settings import UnityUdpSettings
from messaging.spell_cast_message import SpellCastMessage
from spells.spell_match import SpellMatch


class UnityUdpTx:
    def __init__(self, logger: Logger, udp_settings: UdpTxSettings, unity_settings: UnityUdpSettings):
        self._logger = logger
        self._settings = unity_settings

        self._udp_tx = UdpTx(logger, udp_settings)

    def on_spell_detected(self, match: SpellMatch) -> None:
        spell_command = self._settings.spell_mappings.get(match.spell_name)

        if spell_command:
            self._udp_tx.send(SpellCastMessage(match.spell_name.upper(), match.accuracy).to_dict())
