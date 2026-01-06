from logging import Logger

from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.spell_cast_message import SpellCastMessage
from spells.spell_match import SpellMatch


class SpellCastUdpTx:
    def __init__(self, logger: Logger, udp_settings: UdpTxSettings):
        self._logger = logger

        self._udp_tx = UdpTx(logger, udp_settings)

    def on_spell_detected(self, match: SpellMatch) -> None:
        self._udp_tx.send(
            SpellCastMessage(
                WandId=match.wand_id,
                WandName=match.wand_name,
                SpellType=match.spell_name.upper(),
                Confidence=match.accuracy,
            ).to_dict()
        )
