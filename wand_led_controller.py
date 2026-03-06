from gamevolt.messaging.udp.udp_tx import UdpTx
from gamevolt.toolkit.timer import Timer
from messaging.messages.wand_led_message import WandLedMessage


class WandLedController:
    def __init__(self, udp_tx: UdpTx) -> None:
        self._udp_tx = udp_tx
        self._timer = Timer(3)
        self._is_led_on = False

    def start(self) -> None:
        self._timer.start()

    def update(self) -> None:
        if self._timer.is_complete:
            self._timer.restart()
            self._is_led_on = not self._is_led_on

            if self._is_led_on:
                # self._udp_tx.send({"tag_id": "E001", "command": "set_tx_enabled", "enabled": False})
                self._udp_tx.send(WandLedMessage("E001", True, 0).to_dict())
            else:
                self._udp_tx.send(WandLedMessage("E001", False, 0).to_dict())
