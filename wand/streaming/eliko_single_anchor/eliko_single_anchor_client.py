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

    `manage_imu` gates all IMU-enable traffic (init CMD0s + post-reboot
    re-enable). Set False when another system (e.g. the RTLS network) owns
    wand IMU state; the anchor then only subscribes and listens.
    """

    _ENABLE_IMU_CMD = "$PEKIO,DC,{seq},CMD0,0x{tag_id},0x00000903\r\n"
    _DISABLE_IMU_CMD = "$PEKIO,DC,{seq},CMD0,0x{tag_id},0x00000000\r\n"
    _GET_TYPE_CMD = "$PEKIO,DC,{seq},GETD,0x{tag_id},type\r\n"
    _SUBSCRIBE_CMD = "$PEKIO,DC,{seq},SPQF,{flag}\r\n"
    _POLL_BATTERY_CMD = "$PEKIO,DC,{seq},GDHR,0x{tag_id},timeout_ms={timeout_ms}\r\n"
    _INIT_CMD_GAP_S = 0.25

    def __init__(
        self,
        logger: Logger,
        transport: SerialTransport,
        tracked_wand_ids: Iterable[str],
        subscribe_flag: str = "P",
        manage_imu: bool = True,
    ) -> None:
        self._logger = logger
        self._transport = transport
        self._tracked_wand_ids = [self._normalise_tag(t) for t in tracked_wand_ids]
        self._subscribe_flag = subscribe_flag
        self._manage_imu = manage_imu
        self._next_seq = 1

    @property
    def line_received(self) -> Event[Callable[[str], None]]:
        return self._transport.line_received

    async def start_async(self) -> None:
        await self._transport.start()
        if self._manage_imu:
            self._logger.info(
                f"ElikoSingleAnchorClient sending init sequence for tags: {self._tracked_wand_ids}"
            )
            # Anchor processes commands serially with ~10-20ms OTA-store latency per
            # CMD0; flooding causes silent drops (only the first CMD0 gets acked).
            # Space inits out so each completes before the next arrives.
            for tag in self._tracked_wand_ids:
                self.send_command(self._ENABLE_IMU_CMD.format(seq=self._alloc_seq(), tag_id=tag))
                await asyncio.sleep(self._INIT_CMD_GAP_S)
        else:
            self._logger.info("ElikoSingleAnchorClient IMU management disabled; skipping CMD0 init.")
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
        if not self._manage_imu:
            return

        normalised = self._normalise_tag(tag)
        if normalised not in self._tracked_wand_ids:
            self._logger.verbose(
                f"Ignoring reboot of untracked wand ({normalised}); not re-enabling IMU."
            )
            return

        self._logger.info(f"Re-enabling IMU on wand ({normalised}) after reboot.")
        self.send_enable_imu(normalised)

    def send_enable_imu(self, tag: str) -> None:
        """Unconditional CMD0 IMU-enable — bypasses the `manage_imu` gate.
        For manual/diagnostic use (e.g. testing whether a stalled PR stream
        resumes on re-enable); automatic traffic goes via `enable_imu`.
        """
        normalised = self._normalise_tag(tag)
        self._logger.info(f"Sending CMD0 IMU-enable to wand ({normalised}).")
        self.send_command(self._ENABLE_IMU_CMD.format(seq=self._alloc_seq(), tag_id=normalised))

    def restart_imu(self, tag: str) -> None:
        """Diagnostic IMU restart per Eliko guidance for the silent PR stall:
        query the tag's data type (GETD; PR should report 3), then cycle the
        stream off (CMD0 0x00000000) and back on (CMD0 0x00000903). Commands
        are spaced like the init sequence to respect the anchor's per-command
        OTA-store latency.
        """
        normalised = self._normalise_tag(tag)
        self._logger.info(f"Restarting IMU on wand ({normalised}): GETD type, CMD0 off, CMD0 on.")
        asyncio.create_task(self._restart_imu_async(normalised))

    async def _restart_imu_async(self, tag_id: str) -> None:
        self.send_command(self._GET_TYPE_CMD.format(seq=self._alloc_seq(), tag_id=tag_id))
        await asyncio.sleep(self._INIT_CMD_GAP_S)
        self.send_command(self._DISABLE_IMU_CMD.format(seq=self._alloc_seq(), tag_id=tag_id))
        await asyncio.sleep(self._INIT_CMD_GAP_S)
        self.send_command(self._ENABLE_IMU_CMD.format(seq=self._alloc_seq(), tag_id=tag_id))

    def poll_battery(self, tag: str, timeout_ms: int = 2000) -> None:
        """Request the wand's battery voltage. The tag answers via the anchor
        with `$PEKIO,AC,123,0x<tag>,GDHR,voltages,0x<millivolts>,OTA` once the
        OTA delivery lands (or not at all if it times out).
        """
        normalised = self._normalise_tag(tag)
        self.send_command(
            self._POLL_BATTERY_CMD.format(seq=self._alloc_seq(), tag_id=normalised, timeout_ms=timeout_ms)
        )

    def _alloc_seq(self) -> str:
        s = f"{self._next_seq:03d}"
        self._next_seq = (self._next_seq + 1) % 256
        return s

    @staticmethod
    def _normalise_tag(tag: str) -> str:
        s = tag.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        return s.upper()
