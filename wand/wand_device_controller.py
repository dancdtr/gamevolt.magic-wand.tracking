import asyncio
from logging import Logger

from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.messages.wand_led_message import WandLedMessage
from messaging.messages.wand_tx_message import WandTxMessage
from wand.tracked_wand import TrackedWand


class WandDeviceController:
    def __init__(self, logger: Logger, udp_tx: UdpTx) -> None:
        self._logger = logger
        self._udp_tx = udp_tx

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def set_wand_led(self, wand: TrackedWand, enabled: bool, sequence_id: int) -> None:
        self._udp_tx.send(WandLedMessage(wand.id, enabled=enabled, sequence_id=sequence_id).to_dict())

    def set_wand_tx(self, wand: TrackedWand, enabled: bool, sequence_id: int) -> None:
        self._udp_tx.send(WandTxMessage(wand.id, enabled=enabled, sequence_id=sequence_id).to_dict())

    # TODO temp
    def play_spell_cast_cue(self, wand: TrackedWand) -> None:
        self.set_wand_led(wand, enabled=True, sequence_id=0)

        async def _turn_off_later() -> None:
            await asyncio.sleep(2)
            self.set_wand_led(wand, False, 0)

        asyncio.create_task(_turn_off_later())
