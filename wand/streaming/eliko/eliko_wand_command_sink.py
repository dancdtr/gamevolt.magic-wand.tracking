from __future__ import annotations

from gamevolt.logging import Logger
from gamevolt.messaging.message import Message
from messaging.messages.wand_led_message import WandLedMessage
from wand.streaming.eliko.configuration.eliko_command_sink_settings import ElikoCommandSinkSettings
from wand.streaming.eliko.eliko_command_client import ElikoCommandClient


class ElikoWandCommandSink:
    """Routes wand commands over an Eliko PEKIO command channel.

    Today only `WandLedMessage(enabled=True)` is mapped (to SET_TAG_LEDH);
    other message types are debug-logged no-ops until Eliko exposes
    equivalents for TX-enable and haptics. Transport-agnostic: works against
    either `ElikoClient` (TCP) or `ElikoSingleAnchorClient` (serial).
    """

    _LED_PULSE_CMD = "$PEKIO,SET_TAG_LEDH,{tag_id},0x{pattern}\r\n"

    def __init__(self, logger: Logger, client: ElikoCommandClient, settings: ElikoCommandSinkSettings) -> None:
        self._logger = logger
        self._client = client
        self._settings = settings

    def send_to_wand(self, wand_id: str, message: Message) -> None:
        self._dispatch(wand_id, message)

    def broadcast_to_wand(self, wand_id: str, message: Message) -> None:
        # Eliko routes commands by tag id internally; broadcast = send.
        self._dispatch(wand_id, message)

    def _dispatch(self, wand_id: str, message: Message) -> None:
        if isinstance(message, WandLedMessage) and message.enabled:
            command = self._LED_PULSE_CMD.format(
                tag_id=wand_id,
                pattern=self._settings.led_pulse_pattern_hex,
            )
            self._client.send_command(command)
            return

        self._logger.debug(
            f"ElikoWandCommandSink: no Eliko mapping for {type(message).__name__} (wand={wand_id}); ignoring."
        )
