# live_wand_preview.py
from __future__ import annotations

import tkinter as tk

from gamevolt.visualisation.visualier import Visualiser
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition
from visualisation.configuration.input_visualiser_settings import InputVisualiserSettings
from visualisation.input_trail import InputTrail
from visualisation.input_trail_visualiser import InputTrailVisualiser


class InputVisualiser:
    def __init__(self, input_source: MotionInputBase, visualiser: Visualiser, settings: InputVisualiserSettings) -> None:
        self._settings = settings

        self._input = input_source
        self._preview = visualiser

        self._trail = InputTrail(max_points=self._settings.trail_max_points)
        self._renderer = InputTrailVisualiser(self._preview, self._trail, self._settings)

        self._running = False
        self._need_draw = False
        self._axes_ids: list[int] = []

        # Redraw axes on resize
        self._preview.canvas.bind("<Configure>", lambda e: self._redraw_axes())

        # Convenience keybindings
        self._preview.root.bind("c", lambda e: self.clear())
        self._preview.root.bind("<Escape>", lambda e: self.stop())

    # ── lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._preview.start()
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
        self._renderer.destroy()
        self._clear_axes()
        self._preview.stop()

    # Call every tick from your main loop
    def update(self) -> None:
        if not self._running:
            return
        try:
            self._preview.update()
        except tk.TclError:
            # Window closed by user
            self.stop()
            return

        if self._need_draw:
            self._renderer.draw()
            self._need_draw = False

    # ── event handlers ───────────────────────────────────────────────────────
    def _on_sample(self, sample: WandPosition) -> None:
        # Expecting sample.x/y in [-1..1]; ignore if missing
        if sample.nx is None or sample.ny is None:
            return
        self._trail.add(sample)
        self._preview.set_status(f"({sample.nx:.2f}, {sample.ny:.2f})")
        self._need_draw = True

    # ── axes overlay ────────────────────────────────────────────────────────
    def _clear_axes(self) -> None:
        for i in self._axes_ids:
            self._preview.canvas.delete(i)
        self._axes_ids.clear()

    def _redraw_axes(self) -> None:
        self._clear_axes()
        if not self._settings.show_axes:
            return

        c = self._preview.canvas
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
        self._renderer.draw()
