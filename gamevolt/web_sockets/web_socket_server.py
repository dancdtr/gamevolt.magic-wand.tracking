import asyncio
import json
from collections.abc import Callable
from http.cookies import SimpleCookie

from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from websockets.legacy.server import WebSocketServerProtocol, serve

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from gamevolt.messaging.message import Message
from gamevolt.web_sockets.configuration.web_socket_server_settings import WebSocketServerSettings
from gamevolt.web_sockets.web_socket_client_meta import WebSocketClientMeta


class WebSocketServer:
    def __init__(
        self,
        logger: Logger,
        settings: WebSocketServerSettings,
    ) -> None:
        self._settings = settings
        self._logger = logger

        self.client_connected: Event[Callable[[WebSocketClientMeta], None]] = Event()
        self.client_disconnected: Event[Callable[[WebSocketClientMeta], None]] = Event()
        self._message_received: Event[Callable[[str], None]] = Event()

        self._clients: dict[str, WebSocketServerProtocol] = {}
        self._server = None

    @property
    def connected_clients(self) -> dict[str, WebSocketServerProtocol]:
        return self._clients

    @property
    def message_received(self) -> Event[Callable[[str], None]]:
        return self._message_received

    async def start_async(self) -> None:
        host = self._settings.web_socket.host
        port = self._settings.web_socket.port

        self._server = await serve(
            ws_handler=self._handler,
            host=host,
            port=port,
            ping_interval=None,
        )
        self._logger.info(f"WebSocket server listening on ws://{host}:{port}.")

    async def stop_async(self) -> None:
        self._logger.info("Stopping server...")
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for ws in list(self._clients.values()):
            try:
                await ws.close(code=1001, reason="Server shutdown")
            except Exception:
                pass

        self._clients.clear()
        self._logger.info("Server stopped.")

    async def send_to_client_async(self, client_id: str, message: Message) -> None:
        client = self._clients.get(client_id)
        if client is not None:
            try:
                await client.send(json.dumps(message.to_dict()))
                self._logger.trace(f"Sent to {client_id}: {message}")
            except Exception as e:
                self._logger.warning(f"Failed to send to {client_id}: {e}")
        else:
            self._logger.warning(f"Client ({client_id}) not found.")

    async def broadcast_async(self, message: Message) -> None:
        for client_id in self._clients.keys():
            await self.send_to_client_async(client_id, message)

    def broadcast(self, message: Message) -> None:
        asyncio.create_task(self.broadcast_async(message))

    def send_to_client(self, client_id: str, message: Message) -> None:
        asyncio.create_task(self.send_to_client_async(client_id, message))

    async def _handler(self, ws: WebSocketServerProtocol, _: str) -> None:
        cookie_hdr = ws.request_headers.get("cookie", "")
        cookie = SimpleCookie()
        cookie.load(cookie_hdr)

        game_id = cookie.get("GameVolt-Id")
        if not game_id:
            await ws.close(code=1008, reason="Missing GameVolt-Id")
            return

        client_id = game_id.value
        if client_id in self._clients:
            await ws.close(code=1008, reason="Duplicate GameVolt-Id")
            return

        version_cookie = cookie.get("GameVolt-Version")
        version = version_cookie.value if version_cookie else "?.?.?"
        host, port = ws.remote_address
        client_meta = WebSocketClientMeta(id=client_id, version=version, host=host, port=port)

        self._clients[client_id] = ws
        self._logger.info(f"Client connected: {client_meta}.")
        self.client_connected.invoke(client_meta)

        try:
            async for raw in ws:
                self._logger.trace(f"Received from {client_meta.id}: {raw}")
                self._message_received.invoke(raw)
        except ConnectionClosedOK:
            pass
        except ConnectionClosedError as ce:
            self._logger.warning(f"Connection error from {client_meta.id}: {ce}")
        finally:
            self._clients.pop(client_id, None)
            self._logger.info(f"Client disconnected: {client_meta}")
            self.client_disconnected.invoke(client_meta)
