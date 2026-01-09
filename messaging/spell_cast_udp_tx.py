from logging import Logger

from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.spell_cast_message import SpellCastMessage
from spells.spell_match import SpellMatch
from visualisation.visualiser_protocol import WandVisualiserProtocol
from visualisation.wand_visualiser import WandVisualiser


class SpellCastUdpTx:
    def __init__(self, logger: Logger, udp_settings: UdpTxSettings, wand_visualiser: WandVisualiserProtocol):
        self._logger = logger

        self._udp_tx = UdpTx(logger, udp_settings)
        self._wand_visualiser: WandVisualiser | None = wand_visualiser if isinstance(wand_visualiser, WandVisualiser) else None

    def on_spell_detected(self, match: SpellMatch) -> None:
        # temp colour hack for debugging
        colour = "00FF00"

        if self._wand_visualiser:
            visualised_wand = self._wand_visualiser._visualised_wands.get(match.wand_id)
            if visualised_wand:
                colour = visualised_wand.colour_settings.line_colour

        self._udp_tx.send(
            SpellCastMessage(WandId=match.wand_id, SpellType=match.spell_name.upper(), Confidence=match.accuracy, Colour=colour).to_dict()
        )
