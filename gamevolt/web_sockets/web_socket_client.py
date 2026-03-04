import asyncio
import json
from collections.abc import Callable
from logging import Logger
from typing import Any

from websockets import State
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK, InvalidStatus

from gamevolt.events.event import Event
from gamevolt.messaging.message import Message
from gamevolt.web_sockets.configuration.web_socket_client_settings import WebSocketClientSettings


class WebSocketClient:
    def __init__(
        self,
        logger: Logger,
        settings: WebSocketClientSettings,
        additional_headers: dict[str, str] = {},
    ) -> None:
        self._additional_headers = additional_headers
        self._settings = settings
        self._logger = logger

        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task[Any] | None = None
        self._ws: ClientConnection | None = None
        self._stop_event = asyncio.Event()

        self.connected: Event[Callable[[], None]] = Event()
        self.disconnected: Event[Callable[[], None]] = Event()
        self.message_received: Event[Callable[[str], None]] = Event()

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and getattr(self._ws, "state", None) is State.OPEN

    async def start_async(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._stop_event.clear()
        self._task = self._loop.create_task(self._update(), name="WebSocketClient")

    async def stop_async(self) -> None:
        self._logger.info("Stopping client…")
        self._stop_event.set()

        if self._ws and self._ws.state is State.OPEN:
            try:
                await self._ws.close(code=1001, reason="client shutdown")
            except Exception:
                pass

        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._logger.info("Client stopped.")

    def send_message(self, message: Message) -> None:
        if not self._loop or not self.is_connected:
            self._logger.debug("Dropping message, client not connected.")
            return
        asyncio.run_coroutine_threadsafe(self.send_message_async(message), self._loop)

    def send_data(self, raw: str) -> None:
        if not self._loop or not self.is_connected:
            self._logger.debug("Dropping message, client not connected.")
            return
        asyncio.run_coroutine_threadsafe(self.send_data_async(raw), self._loop)

    async def send_message_async(self, message: Message) -> None:
        if not self._loop or not self.is_connected:
            self._logger.debug("Dropping message, client not connected.")
            return
        await self.send_data_async(json.dumps(message.to_dict()))

    async def send_data_async(self, data: str) -> None:
        if not self.is_connected or self._ws is None:
            self._logger.debug("Dropping message, socket not open.")
            return
        try:
            await self._ws.send(data)
        except Exception as e:
            self._logger.error(f"Failed to send message: {e}")

    async def _update(self) -> None:
        interval = self._settings.reconnection_interval
        url = self._settings.web_socket.url
        timeout = self._settings.timeout

        try:
            while not self._stop_event.is_set():
                try:
                    self._logger.info(f"Connecting to {url}…")
                    self._ws = await asyncio.wait_for(
                        connect(
                            url,
                            additional_headers=self._additional_headers,
                            ping_interval=None,
                            open_timeout=timeout,
                            close_timeout=timeout,
                        ),
                        timeout=timeout + 1,
                    )
                    self._logger.info("WebSocket connection established.")
                    self.connected.invoke()

                    while not self._stop_event.is_set():
                        raw = await self._ws.recv()
                        self.message_received.invoke(raw)

                except (ConnectionClosedOK, ConnectionClosedError):
                    self.disconnected.invoke()
                    self._logger.warning("WebSocket closed, will attempt reconnect.")
                except asyncio.TimeoutError:
                    self._logger.error("Connection attempt timed out.")
                except InvalidStatus as e:
                    self._logger.error(f"Handshake failed: {e}")
                except OSError as e:
                    self._logger.error(f"TCP connect failed: {e}")
                finally:
                    if self._ws and self._ws.state is not State.CLOSED:
                        try:
                            await self._ws.close(code=1001, reason="shutdown")
                        except Exception:
                            pass
                    self._ws = None

                if self._stop_event.is_set():
                    break

                self._logger.info(f"Reconnecting in {interval} seconds…")
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
                except asyncio.TimeoutError:
                    pass

        except asyncio.CancelledError:
            self._logger.debug("WebSocketClient _update cancelled.")
        finally:
            if self._ws and self._ws.state is not State.CLOSED:
                try:
                    await self._ws.close(code=1001, reason="shutdown")
                except Exception:
                    pass
            self._ws = None
            self._logger.info("Exiting WebSocketClient background task.")
