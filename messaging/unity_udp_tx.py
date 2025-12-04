from logging import Logger

from gamevolt.messaging.udp.configuration.udp_peer_settings import UdpPeerSettings
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.configuration.unity_udp_settings import UnityUdpSettings
from spells.spell_match import SpellMatch
from spells.spell_type import SpellType


class UnityUdpTx:
    def __init__(self, logger: Logger, udp_settings: UdpTxSettings, unity_settings: UnityUdpSettings):
        self._logger = logger
        self._settings = unity_settings

        self._udp_tx = UdpTx(logger, udp_settings)

    def on_spell_detected(self, spell: SpellMatch) -> None:
        spell_command = self._settings.spell_mappings.get(spell.spell_name)

        if spell_command:
            payload = f"{spell_command}"
            self._udp_tx.send_str(payload)
