# wand_visualiser.py
from __future__ import annotations

import tkinter as tk
from logging import Logger

from gamevolt.visualisation.axes import Axes
from gamevolt.visualisation.label_factory import LabelFactory
from gamevolt.visualisation.visualiser import Visualiser
from visualisation.configuration.trail_settings import TrailColourSettings
from visualisation.configuration.visualised_wand_factory import VisualisedWandFactory
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.coordinate_mode import CoordinateMode
from visualisation.visualised_wand import VisualisedWand
from visualisation.visualiser_protocol import WandVisualiserProtocol
from wand.configuration.input_settings import InputSettings
from wand.tracked_wand_manager import TrackedWandManager


class WandVisualiser(Visualiser, WandVisualiserProtocol):
    def __init__(
        self,
        logger: Logger,
        wand_visualiser_settings: WandVisualiserSettings,
        input_settings: InputSettings,
        visualised_wand_factory: VisualisedWandFactory,
        tracked_wand_manager: TrackedWandManager,
    ) -> None:
        super().__init__(logger, wand_visualiser_settings.visualiser)
        self._wand_visualiser_settings = wand_visualiser_settings
        self._input_settings = input_settings

        self._visualised_wand_factory = visualised_wand_factory
        self._tracked_wand_manager = tracked_wand_manager

        self._status = LabelFactory(wand_visualiser_settings.label, self._root).create()
        self._axes = Axes(wand_visualiser_settings.axes, canvas=self.canvas)

        self._visualised_wands: list[VisualisedWand] = []

        self._is_drawing = True

    def start(self) -> None:
        super().start()

        self.register_key_callback("c", self.clear)
        self.register_key_callback("d", self._on_toggle_drawing)

        self._visualised_wands = self._create_visualised_wands()

        for wand in self._visualised_wands:
            wand.start()

        self._axes.draw()

    def stop(self) -> None:
        super().stop()

        for wand in self._visualised_wands:
            wand.stop()

        self.unregister_key_callbacks("c")
        self.unregister_key_callbacks("d")

        self._axes.clear()

    def update(self) -> None:
        try:
            super().update()
        except tk.TclError:
            super()._on_quit()
            return

        self.draw()

    def set_status(self, status: str) -> None:
        self._status.config(text=status)

    def clear(self) -> None:
        for wand in self._visualised_wands:
            wand.clear_trail()

        self._axes.draw()

    def draw(self) -> None:
        self._axes.draw()
        if self._canvas.winfo_width() <= 1 or self._canvas.winfo_height() <= 1:
            self._canvas.update_idletasks()

        w = max(self._canvas.winfo_width(), 1)
        h = max(self._canvas.winfo_height(), 1)

        for wand in self._visualised_wands:
            wand.erase()

        if not self._is_drawing:
            return

        for wand in self._visualised_wands:
            pts = wand.points()
            n = len(pts)

            if n == 0:
                if wand.line_id is not None:
                    self._canvas.coords(wand.line_id, ())
                return

            coords: list[float] = []
            for nx, ny in pts:
                x, y = self._position_to_canvas(nx, ny, w, h)
                coords.extend([x, y])

            line_colour = wand.colour_settings.line_color
            point_colour = wand.colour_settings.point_colour
            line_width = self._wand_visualiser_settings.trail.line_width
            point_radius = self._wand_visualiser_settings.trail.point_radius

            if n >= 2:
                if wand.line_id is None:
                    wand.line_id = self._canvas.create_line(
                        *coords,
                        fill=line_colour,
                        width=line_width,
                        smooth=self._wand_visualiser_settings.trail.smooth,
                        splinesteps=12 if self._wand_visualiser_settings.trail.smooth else 1,
                    )
                else:
                    self._canvas.coords(wand.line_id, *coords)
                    self._canvas.itemconfig(
                        wand.line_id,
                        fill=line_colour,
                        width=line_width,
                        smooth=self._wand_visualiser_settings.trail.smooth,
                        splinesteps=12 if self._wand_visualiser_settings.trail.smooth else 1,
                    )
            else:
                if wand.line_id is not None:
                    self._canvas.delete(wand.line_id)
                    wand.line_id = None

            if self._wand_visualiser_settings.trail.draw_points:
                r = point_radius
                it = iter(coords)
                for x, y in zip(it, it):
                    wand.dot_ids.append(
                        self._canvas.create_oval(
                            x - r,
                            y - r,
                            x + r,
                            y + r,
                            fill=point_colour,
                            outline=point_colour,
                        )
                    )

    def _on_resize_window(self) -> None:
        super()._on_resize_window()
        self.draw()
        # self._redraw_axes()

    def _on_toggle_drawing(self) -> None:
        self._is_drawing = not self._is_drawing
        self.clear()

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

    def _create_visualised_wands(self) -> list[VisualisedWand]:
        fallback_settings = TrailColourSettings("#ffffff", "ffffff")
        colour_settings = {wand.id: wand.colour for wand in self._input_settings.tracked_wands}

        wands = []
        for wand in self._tracked_wand_manager.tracked_wands():
            settings = colour_settings.get(wand.id, fallback_settings)
            wands.append(self._visualised_wand_factory.create(settings, wand, self._canvas))

        return wands
