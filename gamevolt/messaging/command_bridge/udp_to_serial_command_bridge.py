from __future__ import annotations

import asyncio
from logging import Logger
from typing import Any

from gamevolt.messaging.command_bridge.configuration.command_bridge_settings import CommandBridgeSettings
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.serial.line_sender_protocol import LineSenderProtocol
from messaging.messages.wand_led_message import WandLedMessage
from messaging.messages.wand_tx_message import WandTxMessage


class UdpToSerialCommandBridge:
    def __init__(
        self, logger: Logger, message_handler: MessageHandler, serial_transport: LineSenderProtocol, settings: CommandBridgeSettings
    ) -> None:
        self._message_handler = message_handler
        self._serial = serial_transport
        self._settings = settings
        self._logger = logger

    async def start_async(self) -> None:
        self._message_handler.subscribe_typed(WandLedMessage, self._on_wand_led_message)
        self._message_handler.subscribe_typed(WandTxMessage, self._on_wand_tx_message)
        await self._message_handler.start_async()

    async def stop_async(self) -> None:
        await self._message_handler.stop_async()
        self._message_handler.subscribe_typed(WandLedMessage, self._on_wand_led_message)
        self._message_handler.subscribe_typed(WandTxMessage, self._on_wand_tx_message)

    def _norm_tag(self, tag_id: Any) -> str:
        if tag_id is None:
            raise ValueError("tag_id is required")

        if isinstance(tag_id, str):
            t = tag_id.strip()
            if t == "*" or t.lower() == "broadcast":
                if not self._settings.allow_broadcast:
                    raise ValueError("broadcast not allowed")
                return "*"
            t = t.lower().removeprefix("0x").upper()
            int(t, 16)
            return t

        if isinstance(tag_id, int):
            if tag_id == 0xFFFF:
                if not self._settings.allow_broadcast:
                    raise ValueError("broadcast not allowed")
                return "*"
            return f"{tag_id:04X}"

        raise ValueError(f"Unsupported tag_id type: {type(tag_id)}")

    def _fire_and_forget_send(self, line: str) -> None:
        async def _run() -> None:
            for _ in range(max(1, self._settings.repeat)):
                await self._serial.send_line_async(line)

        asyncio.create_task(_run())

    def _on_wand_led_message(self, message: WandLedMessage) -> None:
        tag = self._norm_tag(message.tag_id)
        seq = int(message.sequence_id)
        if not (0 <= seq <= 255):
            self._logger.warning("Invalid sequence_id=%s for WandLedMessage", seq)
            return

        line = f"led {tag} {1 if message.enabled else 0} {seq}"
        self._logger.info("UDP msg -> SERIAL '%s' (repeat=%d)", line, self._settings.repeat)
        self._fire_and_forget_send(line)

    def _on_wand_tx_message(self, message: WandTxMessage) -> None:
        tag = self._norm_tag(message.tag_id)
        line = f"tx {tag} {1 if message.enabled else 0}"
        self._logger.info("UDP msg -> SERIAL '%s' (repeat=%d)", line, self._settings.repeat)
        self._fire_and_forget_send(line)
