from __future__ import annotations

import json
import traceback
from logging import Logger
from typing import Any, Callable, TypeVar, overload

from gamevolt.events.event_handler import EventHandler
from gamevolt.messaging.message import Message
from gamevolt.messaging.message_receiver_protocol import MessageReceiverProtocol

TMsg = TypeVar("TMsg", bound=Message)


class MessageHandler(EventHandler[type[Message], Callable[[Message], None]]):
    def __init__(self, logger: Logger, message_receiver: MessageReceiverProtocol) -> None:
        super().__init__(logger)
        self._receiver = message_receiver

    async def start_async(self) -> None:
        self._receiver.message_received.subscribe(self._on_data_received)
        await self._receiver.start_async()

    async def stop_async(self) -> None:
        await self._receiver.stop_async()
        self._receiver.message_received.unsubscribe(self._on_data_received)

    def _key_name(self, key: type[Message]) -> str:
        return key.__name__

    def subscribe_typed(self, key: type[TMsg], callback: Callable[[TMsg], None]) -> None:
        super().subscribe(key, callback)  # type: ignore[arg-type]

    def unsubscribe_typed(self, key: type[TMsg], callback: Callable[[TMsg], None]) -> None:
        super().unsubscribe(key, callback)  # type: ignore[arg-type]

    def _on_data_received(self, json_string: str) -> None:
        try:
            json_content = json.loads(json_string)
            message_type = json_content.get("MessageType")
            if message_type is None:
                self._logger.warning(f"Unknown message type: {json_string}\n Key of 'MessageType' not found.")
                return

            self._logger.debug(f"{message_type} received: {json_content}")

            message_class = next((cls for cls in self._subscriptions if cls.__name__ == message_type), None)
            if message_class:
                message = message_class.from_dict(json_content)
                self.notify(message_class, message)
            else:
                self._logger.warning(f"No handler registered for message type: '{message_type}'.")
        except Exception as ex:
            self._logger.error("Error processing JSON: %s\nStack Trace: %s", ex, traceback.format_exc())
