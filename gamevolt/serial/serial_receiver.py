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
        self._running: bool = False

        self.data_received = Event[Callable[[str], None]]()

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

                    if not self._running:
                        break

                    self._logger.info(
                        f"Connection lost on '{self._settings.port}'; "
                        f"will attempt to reconnect in {self._settings.retry_interval:.1f} seconds..."
                    )
                    await asyncio.sleep(self._settings.retry_interval)
                    continue

                if not raw:
                    self._logger.warning(f"Empty read from serial port '{self._settings.port}' - treating as disconnect.")

                    await self._close_streams()

                    if not self._running:
                        break

                    self._logger.info(
                        f"Connection lost on '{self._settings.port}', attempting reconnect in {self._settings.retry_interval:.1f} seconds..."
                    )
                    await asyncio.sleep(self._settings.retry_interval)
                    continue

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                self._logger.debug(f"Received from '{self._settings.port}': {line}")

                try:
                    self.data_received.invoke(line)
                except Exception as ex:  # noqa: BLE001
                    self._logger.exception(f"Error in SerialReceiver data_received handler: {ex}")

        except asyncio.CancelledError:
            pass
        finally:
            self._logger.debug(f"Exiting SerialReceiver main loop for port '{self._settings.port}'...")
            await self._close_streams()
            self._read_task = None

    async def _close_streams(self) -> None:
        if self._writer is not None:
            self._writer.close()
            with suppress(Exception):
                await self._writer.wait_closed()

        self._reader = None
        self._writer = None
