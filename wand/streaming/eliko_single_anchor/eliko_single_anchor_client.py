from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from gamevolt.serial.serial_transport import SerialTransport


class ElikoSingleAnchorClient:
    """Eliko command/data channel over a USB-serial connection to a single anchor.

    Anchor enumerates as a virtual COM port. On start, sends the init sequence
    that enables IMU sampling (one CMD0 per tracked tag) and subscribes to PR
    packets. Exposes a transport-agnostic `send_command` so `ElikoWandCommandSink`
    can run unchanged.

    Init commands are queued on the underlying `SerialTransport`'s TX queue;
    they will be drained once the writer is up. The transport currently has no
    `connected` event, so commands are sent once at start; reconnects will not
    re-fire the init sequence today.
    """

    _ENABLE_IMU_CMD = "$PEKIO,DC,{seq},CMD0,0x{tag_id},0x00000903\r\n"
    _SUBSCRIBE_CMD = "$PEKIO,DC,{seq},SPQF,{flag}\r\n"
    _INIT_CMD_GAP_S = 0.25

    def __init__(
        self,
        logger: Logger,
        transport: SerialTransport,
        tracked_wand_ids: Iterable[str],
        subscribe_flag: str = "P",
    ) -> None:
        self._logger = logger
        self._transport = transport
        self._tracked_wand_ids = [self._normalise_tag(t) for t in tracked_wand_ids]
        self._subscribe_flag = subscribe_flag
        self._next_seq = 1

    @property
    def line_received(self) -> Event[Callable[[str], None]]:
        return self._transport.line_received

    async def start_async(self) -> None:
        await self._transport.start()
        self._logger.info(
            f"ElikoSingleAnchorClient sending init sequence for tags: {self._tracked_wand_ids}"
        )
        # Anchor processes commands serially with ~10-20ms OTA-store latency per
        # CMD0; flooding causes silent drops (only the first CMD0 gets acked).
        # Space inits out so each completes before the next arrives.
        for tag in self._tracked_wand_ids:
            self.send_command(self._ENABLE_IMU_CMD.format(seq=self._alloc_seq(), tag_id=tag))
            await asyncio.sleep(self._INIT_CMD_GAP_S)
        self.send_command(
            self._SUBSCRIBE_CMD.format(seq=self._alloc_seq(), flag=self._subscribe_flag)
        )

    async def stop_async(self) -> None:
        await self._transport.stop()

    def send_command(self, command: str) -> None:
        asyncio.create_task(self._transport.send_line_async(command))

    def enable_imu(self, tag: str) -> None:
        """Send the per-tag CMD0 IMU-enable. Used to recover after a wand
        reboot — CMD0 is volatile on the wand, so any boot drops PR until
        we re-issue it. See `docs/spec.md` §4.5 for the firmware brown-out
        background.
        """
        normalised = self._normalise_tag(tag)
        self._logger.info(f"Re-enabling IMU on wand ({normalised}) after reboot.")
        self.send_command(self._ENABLE_IMU_CMD.format(seq=self._alloc_seq(), tag_id=normalised))

    def _alloc_seq(self) -> str:
        s = f"{self._next_seq:03d}"
        self._next_seq += 1
        return s

    @staticmethod
    def _normalise_tag(tag: str) -> str:
        s = tag.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        return s.upper()
