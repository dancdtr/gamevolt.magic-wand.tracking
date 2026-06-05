from __future__ import annotations

from gamevolt.logging import Logger
from gamevolt.messaging.message import Message
from messaging.messages.wand_haptic_sequence_message import WandHapticSequenceMessage
from messaging.messages.wand_led_message import WandLedMessage
from wand.streaming.eliko.configuration.eliko_command_sink_settings import ElikoCommandSinkSettings
from wand.streaming.eliko.eliko_command_client import ElikoCommandClient
from wand.streaming.eliko.pekio_client import Color, PekioClient


class ElikoWandCommandSink:
    """Routes wand commands over an Eliko PEKIO command channel.

    Translates internal `Message` types into PEKIO commands via `PekioClient`:

    - `WandLedMessage(enabled=True)`  → `client.blink_fast(led_color)`
    - `WandLedMessage(enabled=False)` → `client.stop()` (fade-mode off; firmware
      default green-blink is not suppressed by a plain CMD1=0)
    - `WandHapticSequenceMessage`     → `client.hwave(*pattern_ids[:3])`

    Transport-agnostic: works against either `ElikoClient` (TCP) or
    `ElikoSingleAnchorClient` (serial). `WandTxMessage` is debug-logged
    and ignored — no Eliko equivalent for TX-enable yet.
    """

    def __init__(self, logger: Logger, client: ElikoCommandClient, settings: ElikoCommandSinkSettings) -> None:
        self._logger = logger
        self._client = client
        self._settings = settings
        self._led_color = self._parse_color(settings.led_pulse_color)
        # PekioClient drives PEKIO command construction; we re-tag per call.
        self._pekio = PekioClient(send_line=client.send_command)

    def send_to_wand(self, wand_id: str, message: Message) -> None:
        self._dispatch(wand_id, message)

    def broadcast_to_wand(self, wand_id: str, message: Message) -> None:
        # Eliko routes commands by tag id internally; broadcast = send.
        self._dispatch(wand_id, message)

    def _dispatch(self, wand_id: str, message: Message) -> None:
        self._pekio.set_tag(f"0x{wand_id}")

        if isinstance(message, WandLedMessage):
            if message.enabled:
                self._pekio.blink_fast(self._led_color)
            else:
                # stop_led: holds LEDs off without disturbing background haptic
                # state (e.g. active-zone vibration). End-of-spell-pulse should
                # not silence an ongoing vibrate cue.
                self._pekio.stop_led()
            return

        if isinstance(message, WandHapticSequenceMessage):
            if not message.pattern_ids:
                return
            self._pekio.hwave(*message.pattern_ids[:3])
            return

        self._logger.debug(
            f"ElikoWandCommandSink: no Eliko mapping for {type(message).__name__} (wand={wand_id}); ignoring."
        )

    @staticmethod
    def _parse_color(spec: str) -> Color:
        result = Color.OFF
        for part in spec.split("|"):
            name = part.strip().upper()
            if not name:
                continue
            try:
                result |= Color[name]
            except KeyError as exc:
                raise ValueError(
                    f"Unknown LED color '{part}' in led_pulse_color='{spec}'. "
                    f"Valid: {[c.name for c in Color]}"
                ) from exc
        return result
