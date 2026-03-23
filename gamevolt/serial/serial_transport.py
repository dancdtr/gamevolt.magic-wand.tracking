# gamevolt/serial/serial_receiver.py
from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import suppress

import serial_asyncio

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from gamevolt.serial.line_sender_protocol import LineSenderProtocol


class SerialTransport(LineReceiverProtocol, LineSenderProtocol):
    def __init__(self, logger: Logger, settings: SerialReceiverSettings) -> None:
        self._line_received: Event[Callable[[str], None]] = Event()

        self._settings = settings
        self._logger = logger

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._read_task: asyncio.Task | None = None
        self._write_task: asyncio.Task | None = None
        self._running: bool = False

        self._tx_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)

    @property
    def line_received(self) -> Event[Callable[[str], None]]:
        return self._line_received

    async def send_line_async(self, line: str) -> None:
        # Always newline-terminate for MCU command parser.
        data = (line.rstrip("\r\n") + "\n").encode("utf-8")

        try:
            self._tx_queue.put_nowait(data)
        except asyncio.QueueFull:
            self._logger.warning("Serial TX queue full; dropping outbound command.")
            return

    async def start(self) -> None:
        if self._read_task is not None and not self._read_task.done():
            self._logger.warning("SerialReceiver is already started!")
            return

        self._logger.debug(f"Starting SerialReceiver (auto-reconnect enabled) on port '{self._settings.port}'...")

        self._running = True
        self._read_task = asyncio.create_task(self._run())

        self._logger.info("SerialReceiver main loop started.")

    async def stop(self) -> None:
        self._logger.debug(f"Stopping SerialReceiver on port '{self._settings.port}'...")

        self._running = False

        if self._read_task:
            self._read_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._read_task
            self._read_task = None

        if self._write_task:
            self._write_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._write_task
            self._write_task = None

        self._logger.info(f"Stopped SerialReceiver on port '{self._settings.port}'.")

    async def _run(self) -> None:
        try:
            while self._running:
                if self._reader is None or self._writer is None:
                    try:
                        self._logger.debug(f"Attempting to open serial port '{self._settings.port}' @ {self._settings.baud}...")

                        self._reader, self._writer = await serial_asyncio.open_serial_connection(
                            url=self._settings.port,
                            baudrate=self._settings.baud,
                        )

                        self._logger.info(f"SerialReceiver connected on port '{self._settings.port}'.")

                        # Start writer loop for this connection
                        if self._write_task is None or self._write_task.done():
                            self._write_task = asyncio.create_task(self._write_loop())

                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        self._logger.error(f"Failed to open serial port '{self._settings.port}': {exc}")

                        if not self._running:
                            break

                        self._logger.info(
                            f"Will retry opening port '{self._settings.port}' in {self._settings.retry_interval:.1f} seconds..."
                        )
                        await asyncio.sleep(self._settings.retry_interval)
                        continue

                try:
                    raw = await self._reader.readline()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self._logger.error(f"Error in SerialReceiver read loop on port '{self._settings.port}': {exc}")

                    await self._close_streams()
                    await asyncio.sleep(self._settings.retry_interval)
                    continue

                if not raw:
                    self._logger.warning(f"Empty read from serial port '{self._settings.port}' - treating as disconnect.")
                    await self._close_streams()
                    await asyncio.sleep(self._settings.retry_interval)
                    continue

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                self._logger.trace(f"Received from '{self._settings.port}': {line}")

                try:
                    self.line_received.invoke(line)
                except Exception as ex:  # noqa: BLE001
                    self._logger.exception(f"Error in SerialReceiver data_received handler: {ex}")

        except asyncio.CancelledError:
            pass
        finally:
            self._logger.debug(f"Exiting SerialReceiver main loop for port '{self._settings.port}'...")
            await self._close_streams()
            self._read_task = None

    async def _write_loop(self) -> None:
        try:
            while self._running:
                data = await self._tx_queue.get()

                if self._writer is None:
                    try:
                        self._tx_queue.put_nowait(data)
                    except asyncio.QueueFull:
                        pass
                    await asyncio.sleep(0.05)
                    continue

                try:
                    self._writer.write(data)
                    await self._writer.drain()
                    self._logger.debug(f"Sent to '{self._settings.port}': {data!r}")
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self._logger.error(f"Error in SerialReceiver write loop on port '{self._settings.port}': {exc}")
                    await self._close_streams()
                    await asyncio.sleep(self._settings.retry_interval)

        except asyncio.CancelledError:
            pass

    async def _close_streams(self) -> None:
        if self._write_task and not self._write_task.done():
            self._write_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._write_task
        self._write_task = None

        if self._writer is not None:
            self._writer.close()
            with suppress(Exception):
                await self._writer.wait_closed()

        self._reader = None
        self._writer = None
