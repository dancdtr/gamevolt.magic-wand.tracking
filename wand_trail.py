# wand_trail.py
from __future__ import annotations

import tkinter as tk
from collections import deque
from typing import Deque, Tuple

from input.wand_position import WandPosition


class WandTrail:
    def __init__(
        self,
        canvas: tk.Canvas,
        max_points: int,
        line_width: int,
        line_color: str,
        smooth: bool,
        draw_points: bool,
        point_radius: int,
        point_colour: str | None = None,
        norm_y_is_math_up: bool = True,
    ) -> None:
        self.canvas = canvas
        self.max_points = max_points
        self.line_width = line_width
        self.line_color = line_color
        self.point_colour = point_colour or line_color
        self.smooth = smooth
        self.draw_points = draw_points
        self.point_radius = point_radius
        self.norm_y_is_math_up = norm_y_is_math_up

        self._points: Deque[Tuple[float, float]] = deque(maxlen=max_points)
        self._line_id: int | None = None
        self._dot_ids: list[int] = []

        self.canvas.bind("<Configure>", lambda e: self.draw())

    def add(self, pos: WandPosition) -> None:
        self._points.append((pos.x, pos.y))

    def clear(self) -> None:
        self._points.clear()
        if self._line_id is not None:
            self.canvas.delete(self._line_id)
            self._line_id = None
        for i in self._dot_ids:
            self.canvas.delete(i)
        self._dot_ids.clear()

    def draw(self) -> None:
        if self.canvas.winfo_width() <= 1 or self.canvas.winfo_height() <= 1:
            self.canvas.update_idletasks()

        w = max(self.canvas.winfo_width(), 1)
        h = max(self.canvas.winfo_height(), 1)

        # clear old dots each frame
        for i in self._dot_ids:
            self.canvas.delete(i)
        self._dot_ids.clear()

        n = len(self._points)
        if n == 0:
            if self._line_id is not None:
                self.canvas.coords(self._line_id, ())
            return

        coords: list[float] = []
        for nx, ny in self._points:
            x, y = self._to_canvas(nx, ny, w, h)
            coords.extend([x, y])

        if n >= 2:
            if self._line_id is None:
                self._line_id = self.canvas.create_line(
                    *coords,
                    fill=self.line_color,
                    width=self.line_width,
                    smooth=self.smooth,
                    splinesteps=12 if self.smooth else 1,
                )
            else:
                self.canvas.coords(self._line_id, *coords)
        else:
            if self._line_id is not None:
                self.canvas.delete(self._line_id)
                self._line_id = None

        if self.draw_points:
            r = self.point_radius
            it = iter(coords)
            for x, y in zip(it, it):
                self._dot_ids.append(self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=self.point_colour, outline=self.point_colour))

    def _to_canvas(self, nx: float, ny: float, w: int, h: int) -> Tuple[float, float]:
        x = nx * w
        y = (1.0 - ny) * h if self.norm_y_is_math_up else ny * h
        return x, y
