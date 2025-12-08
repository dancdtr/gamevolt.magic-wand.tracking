# live_wand_preview.py
from __future__ import annotations

import tkinter as tk
from logging import Logger

from gamevolt.visualisation.axes import Axes
from gamevolt.visualisation.label_factory import LabelFactory
from gamevolt.visualisation.visualiser import Visualiser
from input.wand_position import WandPosition
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.coordinate_mode import CoordinateMode
from visualisation.trail import Trail
from visualisation.visualiser_protocol import WandVisualiserProtocol


class WandVisualiser(Visualiser, WandVisualiserProtocol):
    def __init__(self, logger: Logger, settings: WandVisualiserSettings) -> None:
        super().__init__(logger, settings.visualiser)

        self._wand_visualiser_settings = settings

        self._trail = Trail(settings=self._wand_visualiser_settings.trail)
        self._status = LabelFactory(settings.label, self._root).create()

        self._need_draw = False

        self._axes = Axes(settings.axes, canvas=self.canvas)

        self._line_id: int | None = None
        self._dot_ids: list[int] = []

        self._is_drawing = True

    def set_status(self, status: str) -> None:
        self._status.config(text=status)

    # ── lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        super().start()

        self.register_key_callback("c", self.clear)
        self.register_key_callback("d", self._on_toggle_drawing)

        self._axes.draw()

    def stop(self) -> None:
        super().stop()

        self.unregister_key_callbacks("c")
        self.unregister_key_callbacks("d")

        self._axes.clear()

    def update(self) -> None:
        try:
            super().update()
        except tk.TclError:
            super()._on_quit()
            return

        if self._need_draw:
            self.draw()
            self._need_draw = False

    # ── event handlers ───────────────────────────────────────────────────────

    def add_position(self, sample: WandPosition) -> None:
        if sample.nx is None or sample.ny is None:
            return

        self._trail.add(sample)
        self.set_status(f"({sample.nx:.2f}, {sample.ny:.2f})")
        self._need_draw = True

    # ── public helpers ───────────────────────────────────────────────────────
    def clear(self) -> None:
        self._trail.clear()
        self._clear_trail_graphics()
        self._axes.draw()

    def draw(self) -> None:
        self._axes.draw()
        if self._canvas.winfo_width() <= 1 or self._canvas.winfo_height() <= 1:
            self._canvas.update_idletasks()

        w = max(self._canvas.winfo_width(), 1)
        h = max(self._canvas.winfo_height(), 1)

        # clear old points
        self._clear_trail_graphics()

        if not self._is_drawing:
            return

        pts = self._trail.points()
        n = len(pts)

        if n == 0:
            if self._line_id is not None:
                self._canvas.coords(self._line_id, ())
            return

        coords: list[float] = []
        for nx, ny in pts:
            x, y = self._position_to_canvas(nx, ny, w, h)
            coords.extend([x, y])

        if n >= 2:
            if self._line_id is None:
                self._line_id = self._canvas.create_line(
                    *coords,
                    fill=self._wand_visualiser_settings.trail.line_color,
                    width=self._wand_visualiser_settings.trail.line_width,
                    smooth=self._wand_visualiser_settings.trail.smooth,
                    splinesteps=12 if self._wand_visualiser_settings.trail.smooth else 1,
                )
            else:
                self._canvas.coords(self._line_id, *coords)
                self._canvas.itemconfig(
                    self._line_id,
                    fill=self._wand_visualiser_settings.trail.line_color,
                    width=self._wand_visualiser_settings.trail.line_width,
                    smooth=self._wand_visualiser_settings.trail.smooth,
                    splinesteps=12 if self._wand_visualiser_settings.trail.smooth else 1,
                )
        else:
            if self._line_id is not None:
                self._canvas.delete(self._line_id)
                self._line_id = None

        if self._wand_visualiser_settings.trail.draw_points:
            r = self._wand_visualiser_settings.trail.point_radius
            it = iter(coords)
            for x, y in zip(it, it):
                self._dot_ids.append(
                    self._canvas.create_oval(
                        x - r,
                        y - r,
                        x + r,
                        y + r,
                        fill=self._wand_visualiser_settings.trail.point_colour or self._wand_visualiser_settings.trail.line_color,
                        outline=self._wand_visualiser_settings.trail.point_colour or self._wand_visualiser_settings.trail.line_color,
                    )
                )

    def _on_resize_window(self) -> None:
        super()._on_resize_window()
        self.draw()
        # self._redraw_axes()

    def _on_toggle_drawing(self) -> None:
        self._is_drawing = not self._is_drawing
        self.clear()

    def _clear_trail_graphics(self) -> None:
        # delete main line
        if self._line_id is not None:
            self._canvas.delete(self._line_id)
            self._line_id = None

        # delete point dots
        for dot_id in self._dot_ids:
            self._canvas.delete(dot_id)
        self._dot_ids.clear()

    def _position_to_canvas(self, nx: float, ny: float, w: int, h: int) -> tuple[float, float]:
        cm = self._wand_visualiser_settings.trail.coords_mode

        if cm is CoordinateMode.CENTRED:
            if self._wand_visualiser_settings.trail.clip_to_bounds:
                nx = max(-1.0, min(1.0, nx))
                ny = max(-1.0, min(1.0, ny))
            m = max(0, self._wand_visualiser_settings.trail.pixel_margin)
            w_eff = max(1, w - 2 * m)
            h_eff = max(1, h - 2 * m)

            x = ((nx + 1.0) * 0.5) * (w_eff - 1) + m
            y = ((1.0 - (ny + 1.0) * 0.5) if self._wand_visualiser_settings.trail.y_up else ((ny + 1.0) * 0.5)) * (h_eff - 1) + m
            return x, y

        elif cm is CoordinateMode.UNIT:
            if self._wand_visualiser_settings.trail.clip_to_bounds:
                nx = max(0.0, min(1.0, nx))
                ny = max(0.0, min(1.0, ny))
            m = max(0, self._wand_visualiser_settings.trail.pixel_margin)
            w_eff = max(1, w - 2 * m)
            h_eff = max(1, h - 2 * m)

            x = nx * (w_eff - 1) + m
            y = ((1.0 - ny) if self._wand_visualiser_settings.trail.y_up else ny) * (h_eff - 1) + m
            return x, y

        else:
            raise ValueError(f"Unknown coords_mode: '{cm}'")
