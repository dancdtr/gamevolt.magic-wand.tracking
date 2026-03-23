from __future__ import annotations

import asyncio
from typing import Any

from gamevolt.logging import Logger
from gamevolt.messaging.command_bridge.configuration.anchor_command_bridge_settings import AnchorCommandBridgeSettings
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.serial.line_sender_protocol import LineSenderProtocol
from messaging.messages.wand_haptic_message import WandHapticMessage
from messaging.messages.wand_haptic_sequence_message import WandHapticSequenceMessage
from messaging.messages.wand_led_message import WandLedMessage
from messaging.messages.wand_tx_message import WandTxMessage


class AnchorCommandBridge:
    def __init__(
        self, logger: Logger, message_handler: MessageHandler, serial_transport: LineSenderProtocol, settings: AnchorCommandBridgeSettings
    ) -> None:
        self._message_handler = message_handler
        self._serial = serial_transport
        self._settings = settings
        self._logger = logger

        self._send_lock = asyncio.Lock()

    def start(self) -> None:
        self._message_handler.subscribe_typed(WandHapticSequenceMessage, self._on_wand_haptic_sequence_message)
        self._message_handler.subscribe_typed(WandHapticMessage, self._on_wand_haptic_message)
        self._message_handler.subscribe_typed(WandLedMessage, self._on_wand_led_message)
        self._message_handler.subscribe_typed(WandTxMessage, self._on_wand_tx_message)

    def stop(self) -> None:
        self._message_handler.unsubscribe_typed(WandHapticSequenceMessage, self._on_wand_haptic_sequence_message)
        self._message_handler.unsubscribe_typed(WandHapticMessage, self._on_wand_haptic_message)
        self._message_handler.unsubscribe_typed(WandLedMessage, self._on_wand_led_message)
        self._message_handler.unsubscribe_typed(WandTxMessage, self._on_wand_tx_message)

    def _norm_tag(self, tag_id: Any) -> str:
        if tag_id is None:
            raise ValueError("tag_id is required")

        if isinstance(tag_id, str):
            t = tag_id.strip()
            if t == "*" or t.lower() == "broadcast":
                return "*"

            t = t.lower().removeprefix("0x").upper()
            int(t, 16)
            return t

        if isinstance(tag_id, int):
            if tag_id == 0xFFFF:
                return "*"
            return f"{tag_id:04X}"

        raise ValueError(f"Unsupported tag_id type: {type(tag_id)}")

    def _fire_and_forget_send(self, line: str) -> None:
        async def _run() -> None:
            async with self._send_lock:
                for _ in range(max(1, self._settings.repeat)):
                    await self._serial.send_line_async(line)

        asyncio.create_task(_run())

    def _on_wand_led_message(self, message: WandLedMessage) -> None:
        tag = self._norm_tag(message.tag_id)
        seq = int(message.sequence_id)

        if not (0 <= seq <= 255):
            self._logger.warning(f"Invalid sequence_id={seq} for WandLedMessage")
            return

        line = f"led {tag} {1 if message.enabled else 0} {seq}"
        self._logger.verbose(f"UDP msg -> SERIAL '{line}' (repeat={self._settings.repeat})")
        self._fire_and_forget_send(line)

    def _on_wand_tx_message(self, message: WandTxMessage) -> None:
        tag = self._norm_tag(message.tag_id)
        line = f"tx {tag} {1 if message.enabled else 0}"
        self._logger.verbose(f"UDP msg -> SERIAL '{line}' (repeat={self._settings.repeat})")
        self._fire_and_forget_send(line)

    def _on_wand_haptic_message(self, message: WandHapticMessage) -> None:
        tag = self._norm_tag(message.tag_id)
        pattern_id = int(message.pattern_id)

        if not (1 <= pattern_id <= 127):
            self._logger.warning(f"Invalid pattern_id={pattern_id} for WandHapticMessage")
            return

        line = f"hplay {tag} {pattern_id}"
        self._logger.verbose(f"UDP msg -> SERIAL '{line}' (repeat={self._settings.repeat})")
        self._fire_and_forget_send(line)

    def _on_wand_haptic_sequence_message(self, message: WandHapticSequenceMessage) -> None:
        tag = self._norm_tag(message.tag_id)

        try:
            patterns = [int(pattern_id) for pattern_id in message.pattern_ids]
        except Exception:
            self._logger.warning(f"Invalid pattern_ids={message.pattern_ids!r} for WandHapticSequenceMessage")
            return

        if not (1 <= len(patterns) <= 8):
            self._logger.warning(f"Invalid pattern count={len(patterns)} for WandHapticSequenceMessage")
            return

        if any(pattern_id < 1 or pattern_id > 127 for pattern_id in patterns):
            self._logger.warning(f"Invalid pattern_ids={patterns} for WandHapticSequenceMessage")
            return

        line = f"hseq {tag} {' '.join(str(pattern_id) for pattern_id in patterns)}"
        self._logger.verbose(f"UDP msg -> SERIAL '{line}' (repeat={self._settings.repeat})")
        self._fire_and_forget_send(line)

    # def _send_line_repeating(self, line: str, repeat: int) -> None:
    #     for i in range(repeat):
    #         self._fire_and_forget_send(line)
