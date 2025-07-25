import asyncio
from asyncio import Task
from collections.abc import Callable
from contextlib import suppress
from logging import Logger

import serial_asyncio

from gamevolt.events.event import Event
from gamevolt.serial.configuration.binary_serial_receiver_settings import BinarySerialReceiverSettings


class BinarySerialReceiver:
    """
    Reads fixed-size binary frames from a serial port using asyncio,
    attempts to reconnect if the serial connection drops.
    """

    def __init__(
        self,
        logger: Logger,
        settings: BinarySerialReceiverSettings,
    ) -> None:
        self._logger = logger
        self._settings = settings

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._read_task: Task | None = None
        self._reconnect_task: Task | None = None

        # Subscribers receive raw bytes frames
        self.data_received = Event[Callable[[bytes], None]]()

    async def start(self) -> None:
        if self._read_task is not None:
            self._logger.warning("BinarySerialReceiver already started")
            return

        await self._open_connection()
        self._read_task = asyncio.create_task(self._read_loop())

    async def _open_connection(self) -> None:
        """Attempt to open the serial port connection."""
        try:
            self._logger.info(f"Opening binary serial on {self._settings.serial.port} @ {self._settings.serial.baud}")
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=self._settings.serial.port, baudrate=self._settings.serial.baud
            )
            self._logger.info("Binary serial connection established")
        except Exception as e:
            self._logger.error(f"Failed opening serial port: {e}")
            await self._schedule_reconnect()

    async def _read_loop(self) -> None:
        """Continuously read fixed-size frames; on error, schedule reconnect."""
        try:
            while self._reader:
                frame = await self._reader.readexactly(self._settings.binary.packet_size)
                self.data_received.invoke(frame)
        except asyncio.IncompleteReadError:
            self._logger.warning("Serial port closed unexpectedly")
        except Exception as e:
            self._logger.error(f"Error in read loop: {e}", exc_info=True)
        finally:
            await self._cleanup_streams()
            await self._schedule_reconnect()

    async def _cleanup_streams(self) -> None:
        """Close reader/writer without touching tasks."""
        if self._writer:
            self._writer.close()
            with suppress(Exception):
                await self._writer.wait_closed()
        self._reader = None
        self._writer = None

    async def _schedule_reconnect(self) -> None:
        """Schedule a reconnect after retry_interval, unless already scheduled."""
        if self._reconnect_task is None or self._reconnect_task.done():
            self._logger.info(f"Reconnecting in {self._settings.serial.retry_interval}s...")
            self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        await asyncio.sleep(self._settings.serial.retry_interval)
        # clear old task
        self._read_task = None
        await self.start()

    async def stop(self) -> None:
        self._logger.info("Stopping binary serial receiver...")
        # cancel read loop
        if self._read_task:
            self._read_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._read_task
            self._read_task = None

        # cancel reconnect
        if self._reconnect_task:
            self._reconnect_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._reconnect_task
            self._reconnect_task = None

        # cleanup streams
        await self._cleanup_streams()
        self._logger.info("BinarySerialReceiver stopped")
