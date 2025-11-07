# mouse_tk_input.py
from __future__ import annotations

import time
from logging import Logger

from gamevolt_debugging import TickMonitor

from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition
from preview import TkPreview, TkPreviewSettings

_INVERT_X = False
_INVERT_Y = True


def _now_ms() -> int:
    return int(time.monotonic() * 1000)


class MouseTkInput(MotionInputBase):
    """
    Normalises the mouse position to [0..1] in canvas space, applies optional axis inversions,
    then emits per-frame deltas via WandPosition. Absolute x/y are included for debugging/preview.
    """

    def __init__(self, logger: Logger, sample_frequency: int) -> None:
        super().__init__(logger)
        self._logger = logger
        self._running = False

        self._prev_x: float | None = None
        self._prev_y: float | None = None

        self._preview = TkPreview(
            TkPreviewSettings(
                title="Mock Wand Input",
                width=800,
                height=800,
                buffer=100,
            )
        )

        self._tick_monitor = TickMonitor()

        self._interval_s = 1.0 / sample_frequency
        self._next_t = time.perf_counter() + self._interval_s

    def start(self) -> None:
        self._running = True
        self._prev_x = None
        self._prev_y = None

        self._preview.start()

    def stop(self) -> None:
        self._preview.stop()
        self._running = False

    def update(self) -> None:
        if not self._running:
            return

        now = time.perf_counter()
        if now < self._next_t:
            return

        # Ensure geometry is realised
        if self._preview.canvas.winfo_width() <= 1 or self._preview.canvas.winfo_height() <= 1:
            self._preview.canvas.update_idletasks()

        # Screen-space pointer
        sx = self._preview.root.winfo_pointerx()
        sy = self._preview.root.winfo_pointery()

        # Canvas origin in screen coords
        tx = self._preview.canvas.winfo_rootx()
        ty = self._preview.canvas.winfo_rooty()

        # Pointer in canvas coords (can be outside)
        px = sx - tx
        py = sy - ty

        w = max(self._preview.canvas.winfo_width(), 1)
        h = max(self._preview.canvas.winfo_height(), 1)

        # Normalised to [0..1] and only when mouse is within window
        nx = px / w
        ny = py / h
        if not (0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0):
            return

        if _INVERT_X:
            nx = 1.0 - nx
        if _INVERT_Y:
            ny = 1.0 - ny

        # Compute deltas against last absolute (normalised) position
        if self._prev_x is None or self._prev_y is None:
            dx = 0.0
            dy = 0.0
        else:
            dx = nx - self._prev_x
            dy = ny - self._prev_y

        self._prev_x = nx
        self._prev_y = ny

        sample = WandPosition(
            ts_ms=_now_ms(),
            x_delta=dx,
            y_delta=dy,
            x=nx,
            y=ny,
        )

        self._tick_monitor.tick()

        self._preview.set_status(f"({sample.x:.2f}, {sample.y:.2f}) | {self._tick_monitor.tick_rate}hz")

        self.position_updated.invoke(sample)

        self._next_t += self._interval_s
        if now - self._next_t > 0.25:
            self._next_t = now + self._interval_s

    def reset(self) -> None:
        pass
