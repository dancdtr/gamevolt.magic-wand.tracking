# mouse_input_tk.py
from __future__ import annotations

import time
import tkinter as tk
from logging import Logger

from gamevolt.toolkit.maths import clamp01
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition

_INVERT_X = False
_INVERT_Y = True


def _get_time() -> int:
    return int(time.monotonic() * 1000)


class MouseTkInput(MotionInputBase):
    def __init__(self, logger: Logger, root: tk.Misc, window: tk.Widget) -> None:
        super().__init__(logger)

        self._root = root
        self._window = window
        self._logger = logger
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def update(self) -> None:
        if not self._running:
            return None

        # Ensure geometry is realised
        if self._window.winfo_width() <= 1 or self._window.winfo_height() <= 1:
            self._window.update_idletasks()

        # Screen-space pointer
        sx = self._root.winfo_pointerx()
        sy = self._root.winfo_pointery()

        # Target widget origin in screen coords
        tx = self._window.winfo_rootx()
        ty = self._window.winfo_rooty()

        # Pointer in widget coords (can be outside)
        px = sx - tx
        py = sy - ty

        w = max(self._window.winfo_width(), 1)
        h = max(self._window.winfo_height(), 1)

        nx = px / w
        ny = py / h

        # if not (0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0):
        #     return

        nx = clamp01(nx)
        ny = clamp01(ny)
        # only invoke when pointer inside

        if _INVERT_X:
            nx = 1 - nx

        if _INVERT_Y:
            ny = 1 - ny

        if nx < 0 or nx > 1 or ny < 0 or ny > 1:
            nx = 0
            ny = 0

        sample = WandPosition(ts_ms=_get_time(), x=nx, y=ny)

        self.position_updated.invoke(sample)
