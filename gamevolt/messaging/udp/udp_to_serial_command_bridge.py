from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from logging import Logger
from typing import Any

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.serial.line_sender_protocol import LineSenderProtocol


@dataclass
class CommandBridgeSettings(SettingsBase):
    repeat: int = 2
    allow_broadcast: bool = True


class UdpToSerialCommandBridge:
    def __init__(
        self,
        logger: Logger,
        udp_rx: UdpRx,
        serial_transport: LineSenderProtocol,
        settings: CommandBridgeSettings | None = None,
    ) -> None:
        self._logger = logger
        self._udp_rx = udp_rx
        self._serial = serial_transport
        self._settings = settings or CommandBridgeSettings()

        self._loop = asyncio.get_running_loop()

        self._udp_rx.datagram_received.subscribe(self._on_udp_message)

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
            int(t, 16)  # validate hex
            return t

        if isinstance(tag_id, int):
            if tag_id == 0xFFFF:
                if not self._settings.allow_broadcast:
                    raise ValueError("broadcast not allowed")
                return "*"
            return f"{tag_id:04X}"

        raise ValueError(f"Unsupported tag_id type: {type(tag_id)}")

    def _build_line(self, payload: dict[str, Any]) -> str:
        command = str(payload.get("command", "")).strip().lower()
        tag = self._norm_tag(payload.get("tag_id"))

        if command in ("set_tx_enabled", "tx"):
            enabled = bool(payload.get("enabled"))
            return f"tx {tag} {1 if enabled else 0}"

        if command in ("set_led", "set_led_mode", "led"):
            enabled = bool(payload.get("enabled"))
            seq = int(payload.get("sequence_id", 0))
            if not (0 <= seq <= 255):
                raise ValueError("sequence_id must be 0..255")
            return f"led {tag} {1 if enabled else 0} {seq}"

        if command in ("set_haptics", "haptics"):
            enabled = bool(payload.get("enabled"))
            pattern = int(payload.get("pattern_id", 0))
            if not (0 <= pattern <= 255):
                raise ValueError("pattern_id must be 0..255")
            return f"haptics {tag} {1 if enabled else 0} {pattern}"

        if command == "help":
            return "help"

        raise ValueError(f"Unknown command '{command}'")

    def _on_udp_message(self, text: str, addr: tuple[str, int]) -> None:
        self._logger.info("UDP RX from %s: %r", addr, text)
        self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self._handle_udp_message_async(text, addr)))

    async def _handle_udp_message_async(self, text: str, addr: tuple[str, int]) -> None:
        try:
            payload = json.loads(text)

            if not isinstance(payload, dict):
                raise ValueError("UDP payload must decode to a JSON object")

            line = self._build_line(payload)

            self._logger.info(f"UDP {addr} -> SERIAL '{line}' (repeat={self._settings.repeat})")

            for _ in range(max(1, self._settings.repeat)):
                await self._serial.send_line_async(line)

        except Exception as exc:
            self._logger.warning(f"Bad UDP command from {addr}: {exc} text={text!r}")
