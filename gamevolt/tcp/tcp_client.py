from __future__ import annotations

import asyncio
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from gamevolt.tcp.configuration.tcp_client_settings import TcpClientSettings


class TcpClient:
    """Generic line-based async TCP client with reconnect.

    Connects to `host:port`, reads CRLF/LF-terminated lines, emits each
    via `line_received` (stripped, ASCII-decoded with replacement for
    bad bytes). `send` writes raw text back; writes are dropped with a
    warning if no connection is up. On disconnect the run loop sleeps
    `reconnect_delay_s` and retries until `stop_async` is called.
    """

    def __init__(self, logger: Logger, settings: TcpClientSettings) -> None:
        self.line_received: Event[Callable[[str], None]] = Event()
        self.disconnected: Event[Callable[[], None]] = Event()
        self.connected: Event[Callable[[], None]] = Event()

        self._settings = settings
        self._logger = logger

        self._writer: asyncio.StreamWriter | None = None
        self._task: asyncio.Task[None] | None = None

    @property
    def is_connected(self) -> bool:
        return self._writer is not None

    async def start_async(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name=f"TcpClient[{self._settings.host}:{self._settings.port}]")

    async def stop_async(self) -> None:
        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await self._close_writer()

    def send(self, data: str) -> None:
        """Fire-and-forget write. Buffers immediately; no backpressure."""
        writer = self._writer
        if writer is None:
            self._logger.warning(f"TcpClient send dropped, no connection: {data.strip()!r}")
            return
        writer.write(data.encode("ascii"))
        self._logger.debug(f"TcpClient sent: {data.strip()}")

    async def send_async(self, data: str) -> None:
        """Write and await drain. Use when the caller needs backpressure
        or is producing from a non-loop thread (via
        `asyncio.run_coroutine_threadsafe`)."""
        writer = self._writer
        if writer is None:
            self._logger.warning(f"TcpClient send dropped, no connection: {data.strip()!r}")
            return
        writer.write(data.encode("ascii"))
        try:
            await writer.drain()
        except Exception as e:
            self._logger.warning(f"TcpClient drain failed: {e!r}")
            return
        self._logger.debug(f"TcpClient sent: {data.strip()}")

    async def _run(self) -> None:
        host = self._settings.host
        port = self._settings.port
        delay_s = self._settings.reconnect_delay_s

        while True:
            try:
                self._logger.info(f"TcpClient connecting to {host}:{port}")
                reader, writer = await asyncio.open_connection(host, port)
                self._writer = writer
                self._logger.info(f"TcpClient connected to {host}:{port}")
                try:
                    self.connected.invoke()
                except Exception:
                    self._logger.exception("TcpClient connected handler crashed")
                await self._read_loop(reader)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._logger.warning(f"TcpClient connection error: {e!r}")
            finally:
                was_connected = self._writer is not None
                await self._close_writer()
                if was_connected:
                    try:
                        self.disconnected.invoke()
                    except Exception:
                        self._logger.exception("TcpClient disconnected handler crashed")

            await asyncio.sleep(delay_s)

    async def _read_loop(self, reader: asyncio.StreamReader) -> None:
        while True:
            raw = await reader.readline()
            if not raw:
                self._logger.info(f"TcpClient {self._settings.host}:{self._settings.port} EOF, will reconnect")
                return
            line = raw.decode("ascii", errors="replace").strip()
            if not line:
                continue
            try:
                self.line_received.invoke(line)
            except Exception:
                self._logger.exception("TcpClient line_received handler crashed")

    async def _close_writer(self) -> None:
        writer = self._writer
        self._writer = None
        if writer is None:
            return
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
