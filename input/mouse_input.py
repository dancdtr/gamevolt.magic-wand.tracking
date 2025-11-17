# mouse_input.py
from __future__ import annotations

import time
import tkinter as tk
from logging import Logger

from gamevolt_debugging import TickMonitor

from gamevolt.visualisation.visualiser import Visualiser
from input.factories.mouse.configuration.mouse_settings import MouseSettings
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition


def _now_ms() -> int:
    return int(time.monotonic() * 1000)


class MouseInput(MotionInputBase):
    """
    Emits WandPosition samples derived from the mouse over a supplied TkPreview canvas.
    - Requires a shared TkPreview (does not create, start, stop, or pump the GUI).
    - Outputs centered coordinates in [-1..1] with +Y up.
    """

    def __init__(self, logger: Logger, settings: MouseSettings, visualiser: Visualiser) -> None:
        super().__init__(logger)
        self._logger = logger
        self._settings = settings
        self._visualiser = visualiser

        self._tick_monitor = TickMonitor()
        self._interval_s = 1.0 / self._settings.sample_frequency
        self._next_t = time.perf_counter() + self._interval_s

        self._prev_x: float | None = None
        self._prev_y: float | None = None

        self._running = False

    async def start(self) -> None:
        self._running = True
        self._prev_x = None
        self._prev_y = None

    def stop(self) -> None:
        self._running = False

    def update(self) -> None:
        if not self._running:
            return

        now = time.perf_counter()
        if now < self._next_t:
            return

        try:
            # Geometry should already be realised by whoever pumps the preview.
            if self._visualiser.canvas.winfo_width() <= 1 or self._visualiser.canvas.winfo_height() <= 1:
                self._visualiser.canvas.update_idletasks()

            # Screen-space pointer
            sx = self._visualiser.root.winfo_pointerx()
            sy = self._visualiser.root.winfo_pointery()

            # Canvas origin in screen coords
            tx = self._visualiser.canvas.winfo_rootx()
            ty = self._visualiser.canvas.winfo_rooty()

            # Pointer in canvas coords (can be outside)
            px = sx - tx
            py = sy - ty

            w = max(self._visualiser.canvas.winfo_width(), 1)
            h = max(self._visualiser.canvas.winfo_height(), 1)

            # Normalised to [0..1] for inside-window test
            nx01 = px / w
            ny01 = py / h
            if not (0.0 <= nx01 <= 1.0 and 0.0 <= ny01 <= 1.0):
                self._next_t = now + self._interval_s
                return

            # Map to centered [-1..1] with +Y up
            cx = (nx01 - 0.5) * 2.0
            cy = (0.5 - ny01) * 2.0

            # Optional inversions (sign flip)
            if self._settings.invert_x:
                cx = -cx
            if self._settings.invert_y:
                cy = -cy

            # Deltas
            if self._prev_x is None or self._prev_y is None:
                dx = 0.0
                dy = 0.0
            else:
                dx = cx - self._prev_x
                dy = cy - self._prev_y

            self._prev_x = cx
            self._prev_y = cy

            sample = WandPosition(
                ts_ms=_now_ms(),
                x_delta=dx,
                y_delta=dy,
                nx=cx,
                ny=cy,
            )

            self._tick_monitor.tick()
            self.position_updated.invoke(sample)

            self._next_t += self._interval_s
            if now - self._next_t > 0.25:
                self._next_t = now + self._interval_s

        except tk.TclError:
            # Window likely closed by the preview owner; stop cleanly
            self.stop()

    def reset(self) -> None:
        self._prev_x = None
        self._prev_y = None
