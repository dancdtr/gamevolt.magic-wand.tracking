# imu_motion_input.py
from __future__ import annotations

import math
import struct
import threading
import time
from dataclasses import dataclass
from logging import Logger
from typing import Callable, Optional

import serial  # pip install pyserial
from serial import Serial
from serial.tools import list_ports

from gamevolt.events.event import Event
from input.imu.configuration.imu_input_settings import ImuInputSettings
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition

# ---------- Packet format from CircuitPython ----------
# <Ihhhhhh = ts_ms (u32), ax_mg, ay_mg, az_mg, gx_0.1dps, gy_0.1dps, gz_0.1dps
_FMT = "<Ihhhhhh"
_PKT_SIZE = struct.calcsize(_FMT)
_U32_MAX = 0xFFFFFFFF


# ---------- Helpers ----------
def _now_ms() -> int:
    return int(time.monotonic() * 1000)


def _u32_dt_ms(curr: int, prev: int) -> int:
    """Unsigned 32-bit wrap-safe delta in ms."""
    return (curr - prev) & _U32_MAX


class ImuInput(MotionInputBase):
    """
    Reads IMU binary from a CircuitPython Feather (LSM6DS3TR-C) and emits per-frame deltas:
      dx = yaw_deg_delta * sens_x
      dy = (-pitch_deg_delta) * sens_y
    Gyro-only 'gyromouse' mapping (no gravity separation needed).
    """

    def __init__(self, logger: Logger, settings: ImuInputSettings) -> None:
        super().__init__(logger)
        self._cfg = settings
        self._ser: Serial | None = None
        self._thread: threading.Thread | None = None
        self._running = False

        # State for integration / downsampling
        self._acc_dx = 0.0
        self._acc_dy = 0.0
        self._last_emit_ms = _now_ms()
        self._emit_period_ms = max(int(1000.0 / settings.emit_hz), 1)

        # For rate smoothing
        self._gz_dps_f = 0.0  # yaw
        self._gy_dps_f = 0.0  # pitch

        self._abs_x = 0.5
        self._abs_y = 0.5

    # ----- lifecycle -----
    def start(self) -> None:
        if self._running:
            return
        port = self._cfg.port or self._autodetect_port()
        if not port:
            raise RuntimeError("IMU serial port not found. Set ImuInputConfig.port explicitly.")

        self._ser = serial.Serial(
            port=port,
            baudrate=self._cfg.baudrate,
            timeout=self._cfg.read_timeout_s,
        )
        self._ser.reset_input_buffer()
        self._running = True
        self._thread = threading.Thread(target=self._worker, name="ImuMotionInput", daemon=True)
        self._thread.start()
        self._logger.info(f"ImuMotionInput started on {port}")

        self._abs_x = 0.5
        self._abs_y = 0.5

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        self._logger.info("ImuMotionInput stopped")

    # The processor doesn’t need to call update(); we push from a thread.
    def update(self) -> None:
        return

    # ----- core worker -----
    def _worker(self) -> None:
        buf = bytearray()
        last_ts_u32: Optional[int] = None

        while self._running and self._ser:
            try:
                chunk = self._ser.read(self._ser.in_waiting or 64)
                if not chunk:
                    # periodic emit check even if no new bytes
                    self._maybe_emit(_now_ms())
                    continue

                buf.extend(chunk)

                while len(buf) >= _PKT_SIZE:
                    pkt = bytes(buf[:_PKT_SIZE])
                    del buf[:_PKT_SIZE]

                    ts_u32, ax_mg, ay_mg, az_mg, gx_ddps, gy_ddps, gz_ddps = struct.unpack(_FMT, pkt)

                    # Convert gyro to dps (then to degrees-per-sample via dt)
                    gx_dps = gx_ddps * 0.1
                    gy_dps = gy_ddps * 0.1
                    gz_dps = gz_ddps * 0.1

                    # Wrap-safe dt
                    if last_ts_u32 is None:
                        last_ts_u32 = ts_u32
                        continue  # need a dt
                    dt_ms = _u32_dt_ms(ts_u32, last_ts_u32)
                    last_ts_u32 = ts_u32

                    # Robustness: if there was a big gap, reset accumulators to avoid jumps
                    if dt_ms > self._cfg.drop_if_large_gap_ms or dt_ms == 0:
                        self._acc_dx = 0.0
                        self._acc_dy = 0.0
                        continue

                    dt_s = dt_ms / 1000.0

                    # Deadband small rates
                    if abs(gz_dps) < self._cfg.deadband_dps:
                        gz_dps = 0.0
                    if abs(gy_dps) < self._cfg.deadband_dps:
                        gy_dps = 0.0

                    # Simple EMA smoothing on rates
                    a = self._cfg.smooth_alpha
                    self._gz_dps_f = (1 - a) * self._gz_dps_f + a * gz_dps
                    self._gy_dps_f = (1 - a) * self._gy_dps_f + a * gy_dps

                    # Integrate to angle deltas (degrees)
                    yaw_deg_delta = self._gz_dps_f * dt_s
                    pitch_deg_delta = self._gy_dps_f * dt_s

                    # Map to 2D deltas (pitch up should usually move cursor "up" => negative screen y)
                    dx = yaw_deg_delta * self._cfg.sens_yaw_deg_to_unit
                    dy = (-pitch_deg_delta) * self._cfg.sens_pitch_deg_to_unit

                    if self._cfg.invert_x:
                        dx = -dx
                    if self._cfg.invert_y:
                        dy = -dy

                    self._acc_dx += dx
                    self._acc_dy += dy

                    # Try to emit at fixed cadence
                    self._maybe_emit(host_ts_ms=_now_ms())

            except Exception as ex:
                self._logger.exception(f"ImuMotionInput worker error: {ex}")
                time.sleep(0.25)

    def _maybe_emit(self, host_ts_ms: int) -> None:
        if host_ts_ms - self._last_emit_ms < self._emit_period_ms:
            return

        dx = max(min(self._acc_dx, self._cfg.max_step), -self._cfg.max_step)
        dy = max(min(self._acc_dy, self._cfg.max_step), -self._cfg.max_step)

        self._acc_dx = 0.0
        self._acc_dy = 0.0
        self._last_emit_ms = host_ts_ms

        # If essentially zero, you can skip emitting to reduce chatter
        if dx == 0.0 and dy == 0.0:
            return

        # Maintain a debug absolute position for UIs (clamped to [0..1])
        self._abs_x = min(max(self._abs_x + dx, 0.0), 1.0)
        self._abs_y = min(max(self._abs_y + dy, 0.0), 1.0)

        sample = WandPosition(
            ts_ms=host_ts_ms,
            x_delta=dx,
            y_delta=dy,
            x=self._abs_x,
            y=self._abs_y,
        )
        self.position_updated.invoke(sample)

    # ----- utilities -----
    def _autodetect_port(self) -> Optional[str]:
        """Try to find an Adafruit Feather nRF52840 serial port automatically."""
        try:
            for p in list_ports.comports():
                desc = (p.description or "").lower()
                hwid = (p.hwid or "").lower()
                # Heuristics: look for Feather/nRF/CircuitPython keywords or known VID/PID
                if any(k in desc for k in ("feather", "nrf", "circuitpython", "adafruit")):
                    return p.device
                if "239a" in hwid:  # Adafruit VID
                    return p.device
        except Exception:
            pass
        return None
