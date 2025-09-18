import asyncio
from collections.abc import Callable
from contextlib import suppress
from logging import Logger

import serial_asyncio

from gamevolt.events.event import Event
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings


class SerialReceiver:
    def __init__(self, logger: Logger, settings: SerialReceiverSettings) -> None:
        self._logger = logger
        self._settings = settings

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._read_task: asyncio.Task | None = None

        self.data_received = Event[Callable[[str], None]]()

    async def start(self) -> None:
        if self._read_task is not None:
            self._logger.warning("SerialReceiver is already started!")
            return

        self._logger.info("Starting SerialReceiver...")

        self._reader, self._writer = await serial_asyncio.open_serial_connection(
            url=self._settings.port,
            baudrate=self._settings.baud,
        )
        self._read_task = asyncio.create_task(self._read_loop())
        self._logger.info("SerialReceiver started.")

    async def _read_loop(self) -> None:
        try:
            while self._reader is not None:
                raw = await self._reader.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", errors="ignore").strip()
                # self._logger.debug(f"Received: {line}")
                self.data_received.invoke(line)

        except asyncio.CancelledError:
            pass

        # except Exception as exc:
        #     self._logger.error(f"Error in read loop: {exc}")

        finally:
            self._logger.debug("Exiting SerialReceiver read loop...")

    async def stop(self) -> None:
        self._logger.info("Stopping SerialReceiver...")
        if self._read_task:
            self._read_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._read_task
            self._read_task = None

        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

        self._logger.info("SerialReceiver stopped.")
