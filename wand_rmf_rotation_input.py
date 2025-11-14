# wand_rmf_motion_input.py
from __future__ import annotations

import asyncio
from logging import Logger
from typing import Callable, Optional

from gamevolt.events.event import Event
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.serial.serial_receiver import SerialReceiver
from input.motion_input_base import MotionInputBase  # your base class
from input.wand.interpreters.configuration.rmf_settings import RMFSettings
from input.wand.interpreters.wand_yawpitch_rmf_interpreter import YawPitchRMFInterpreter
from input.wand_position import WandPosition
from wand_data_reader import WandDataMessage, WandDataReader


class WandRMFMotionInput(MotionInputBase):
    """
    Motion input that consumes anchor 'PKT/DATA' yaw/pitch batches, applies
    a Rotation-Minimizing Frame (RMF) to produce roll-invariant, pole-stable
    Δx/Δy, and emits WandPosition via MotionInputBase.position_updated.

    Lifecycle:
      await start()  -> sets up SerialReceiver + reader + interpreter
      await stop()

    Controls:
      relock_frame_now()         -> lock RMF using last received yaw/pitch
      relock_frame(yaw, pitch)   -> lock RMF using explicit angles (deg)
      zero_absolute()            -> zero the integrated absolute x,y
    """

    def __init__(
        self,
        logger: Logger,
        serial_reader: SerialReceiver,
        wand_data_reader: WandDataReader,
        rmf_settings: Optional[RMFSettings] = None,
        autolock_on_first: bool = True,
    ) -> None:
        super().__init__(logger)

        self._serial_reader = serial_reader
        self._wand_data_reader = wand_data_reader
        self._interp = YawPitchRMFInterpreter(rmf_settings or RMFSettings())

        self._wand_data_reader.wand_position_updated.subscribe(self._on_wand_data)
        self._interp.position_updated.subscribe(self._forward_position)

        self._autolock_on_first = autolock_on_first
        self._locked = False
        self._want_relock_on_next = False

        self._last_yaw_deg: Optional[float] = None
        self._last_pitch_deg: Optional[float] = None

    # ── public API ──────────────────────────────────────────────────────────

    def start(self) -> None:
        self._wand_data_reader.start()

    def stop(self) -> None:
        self._wand_data_reader.stop()

    def update(self) -> None:
        pass

    def relock_frame_now(self) -> None:
        """Lock RMF using the most recent yaw/pitch (if available)."""
        if self._last_yaw_deg is None or self._last_pitch_deg is None:
            # fallback: lock on next sample
            self._want_relock_on_next = True
            return
        self.relock_frame(self._last_yaw_deg, self._last_pitch_deg)

    def relock_frame(self, yaw_deg: float, pitch_deg: float) -> None:
        """Lock RMF using explicit yaw/pitch in degrees."""
        self._interp.lock_frame_from_yawpitch(yaw_deg, pitch_deg)
        self._interp.zero_absolute()  # optional; remove if you want to preserve cursor
        self._locked = True
        self._want_relock_on_next = False
        self._logger.info(f"RMF locked at yaw={yaw_deg:.2f}°, pitch={pitch_deg:.2f}°")

    def zero_absolute(self) -> None:
        """Zero the integrated absolute cursor."""
        self._interp.zero_absolute()

    # ── internals ───────────────────────────────────────────────────────────

    def _on_wand_data(self, m: WandDataMessage) -> None:
        # Remember last angles for optional relock_now()
        self._last_yaw_deg = m.yaw
        self._last_pitch_deg = m.pitch

        # First sample auto-lock (or relock requested)
        if (self._autolock_on_first and not self._locked) or self._want_relock_on_next:
            self.relock_frame(m.yaw, m.pitch)

        # Feed interpreter
        self._interp.on_sample(m.ms, m.yaw, m.pitch)

    def _forward_position(self, pos: WandPosition) -> None:
        # Re-emit via base class event
        self.position_updated.invoke(pos)
