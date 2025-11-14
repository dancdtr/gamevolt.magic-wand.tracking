# live_wand_preview.py
from __future__ import annotations

import tkinter as tk

from gamevolt.visualisation.visualier import Visualiser
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition
from visualisation.configuration.input_visualiser_settings import InputVisualiserSettings
from visualisation.coordinate_mode import CoordinateMode
from visualisation.input_trail import InputTrail


class InputVisualiser:
    def __init__(self, input_source: MotionInputBase, visualiser: Visualiser, settings: InputVisualiserSettings) -> None:
        self._settings = settings

        self._input = input_source
        self._visualiser = visualiser
        self._canvas = visualiser.canvas

        self._trail = InputTrail(max_points=self._settings.trail_max_points)

        self._running = False
        self._need_draw = False
        self._axes_ids: list[int] = []

        self._line_id: int | None = None
        self._dot_ids: list[int] = []

        # Convenience keybindings
        self._visualiser.root.bind("c", lambda e: self.clear())
        self._visualiser.root.bind("<Escape>", lambda e: self.stop())

        # Redraw on resize
        self._visualiser.canvas.bind("<Configure>", lambda e: self.draw())
        self._visualiser.canvas.bind("<Configure>", lambda e: self._redraw_axes())

    # ── lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._visualiser.start()
        self._input.position_updated.subscribe(self._on_sample)
        self._redraw_axes()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        try:
            self._input.position_updated.unsubscribe(self._on_sample)  # if your event supports it
        except Exception:
            pass
        self._destroy()
        self._clear_axes()
        self._visualiser.stop()

    # Call every tick from your main loop
    def update(self) -> None:
        if not self._running:
            return
        try:
            self._visualiser.update()
        except tk.TclError:
            # Window closed by user
            self.stop()
            return

        if self._need_draw:
            self.draw()
            self._need_draw = False

    # ── event handlers ───────────────────────────────────────────────────────
    def _on_sample(self, sample: WandPosition) -> None:
        # Expecting sample.x/y in [-1..1]; ignore if missing
        if sample.nx is None or sample.ny is None:
            return
        self._trail.add(sample)
        self._visualiser.set_status(f"({sample.nx:.2f}, {sample.ny:.2f})")
        self._need_draw = True

    # ── axes overlay ────────────────────────────────────────────────────────
    def _clear_axes(self) -> None:
        for i in self._axes_ids:
            self._visualiser.canvas.delete(i)
        self._axes_ids.clear()

    def _redraw_axes(self) -> None:
        self._clear_axes()
        if not self._settings.show_axes:
            return

        c = self._visualiser.canvas
        w = max(c.winfo_width(), 1)
        h = max(c.winfo_height(), 1)
        cx = w // 2
        cy = h // 2

        # Crosshair through the centre (matches centered coords)
        self._axes_ids.append(c.create_line(0, cy, w, cy, fill=self._settings.axes_color, width=self._settings.axes_width))
        self._axes_ids.append(c.create_line(cx, 0, cx, h, fill=self._settings.axes_color, width=self._settings.axes_width))

        # Optional border
        self._axes_ids.append(c.create_rectangle(1, 1, w - 1, h - 1, outline=self._settings.axes_color, width=self._settings.axes_width))

    # ── public helpers ───────────────────────────────────────────────────────
    def clear(self) -> None:
        self._trail.clear()
        self.draw()

    # ── input position helpers ───────────────────────────────────────────────────────

    def _destroy(self) -> None:
        if self._line_id is not None:
            self._canvas.delete(self._line_id)
            self._line_id = None
        for i in self._dot_ids:
            self._canvas.delete(i)
        self._dot_ids.clear()

    def _position_to_canvas(self, nx: float, ny: float, w: int, h: int) -> tuple[float, float]:
        cm = self._settings.coords_mode

        if cm is CoordinateMode.CENTRED:
            if self._settings.clip_to_bounds:
                nx = max(-1.0, min(1.0, nx))
                ny = max(-1.0, min(1.0, ny))
            m = max(0, self._settings.pixel_margin)
            w_eff = max(1, w - 2 * m)
            h_eff = max(1, h - 2 * m)

            x = ((nx + 1.0) * 0.5) * (w_eff - 1) + m
            y = ((1.0 - (ny + 1.0) * 0.5) if self._settings.y_up else ((ny + 1.0) * 0.5)) * (h_eff - 1) + m
            return x, y

        elif cm is CoordinateMode.UNIT:
            if self._settings.clip_to_bounds:
                nx = max(0.0, min(1.0, nx))
                ny = max(0.0, min(1.0, ny))
            m = max(0, self._settings.pixel_margin)
            w_eff = max(1, w - 2 * m)
            h_eff = max(1, h - 2 * m)

            x = nx * (w_eff - 1) + m
            y = ((1.0 - ny) if self._settings.y_up else ny) * (h_eff - 1) + m
            return x, y

        else:
            raise ValueError(f"Unknown coords_mode: '{cm}'")

    def draw(self) -> None:
        if self._canvas.winfo_width() <= 1 or self._canvas.winfo_height() <= 1:
            self._canvas.update_idletasks()

        w = max(self._canvas.winfo_width(), 1)
        h = max(self._canvas.winfo_height(), 1)

        # clear old points
        for i in self._dot_ids:
            self._canvas.delete(i)
        self._dot_ids.clear()

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
                    fill=self._settings.line_color,
                    width=self._settings.line_width,
                    smooth=self._settings.smooth,
                    splinesteps=12 if self._settings.smooth else 1,
                )
            else:
                self._canvas.coords(self._line_id, *coords)
                self._canvas.itemconfig(
                    self._line_id,
                    fill=self._settings.line_color,
                    width=self._settings.line_width,
                    smooth=self._settings.smooth,
                    splinesteps=12 if self._settings.smooth else 1,
                )
        else:
            if self._line_id is not None:
                self._canvas.delete(self._line_id)
                self._line_id = None

        if self._settings.draw_points:
            r = self._settings.point_radius
            it = iter(coords)
            for x, y in zip(it, it):
                self._dot_ids.append(
                    self._canvas.create_oval(
                        x - r,
                        y - r,
                        x + r,
                        y + r,
                        fill=self._settings.point_colour or self._settings.line_color,
                        outline=self._settings.point_colour or self._settings.line_color,
                    )
                )
