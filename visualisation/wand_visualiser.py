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
from visualisation.wand_colour_assigner import WandColourAssigner
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

        self._visualised_wands: dict[str, VisualisedWand] = {}
        self._is_drawing = True

        # New: colour allocator from settings palette
        self._colour_assigner = WandColourAssigner(self._wand_visualiser_settings.colours)

    def start(self) -> None:
        super().start()

        self.register_key_callback("c", self.clear)
        self.register_key_callback("d", self._on_toggle_drawing)

        self._sync_visualised_wands()

        for vw in self._visualised_wands.values():
            vw.start()

        self._axes.draw()

    def stop(self) -> None:
        super().stop()

        for wand_id, vw in list(self._visualised_wands.items()):
            vw.dispose()
        self._visualised_wands.clear()
        self._colour_assigner.reset()

        self.unregister_key_callbacks("c")
        self.unregister_key_callbacks("d")

        self._axes.clear()

    def update(self) -> None:
        try:
            super().update()
        except tk.TclError:
            super()._on_quit()
            return

        # main loop drives updates elsewhere (as you said), so just sync visuals here
        self._sync_visualised_wands()
        self.draw()

    def set_status(self, status: str) -> None:
        self._status.config(text=status)

    def clear(self) -> None:
        for vw in self._visualised_wands.values():
            vw.clear_trail()
        self._axes.draw()

    def draw(self) -> None:
        self._axes.draw()
        if self._canvas.winfo_width() <= 1 or self._canvas.winfo_height() <= 1:
            self._canvas.update_idletasks()

        w = max(self._canvas.winfo_width(), 1)
        h = max(self._canvas.winfo_height(), 1)

        for vw in self._visualised_wands.values():
            vw.erase()

        if not self._is_drawing:
            return

        for vw in self._visualised_wands.values():
            pts = vw.points()
            n = len(pts)

            if n == 0:
                if vw.line_id is not None:
                    self._canvas.coords(vw.line_id, ())
                continue

            coords: list[float] = []
            for nx, ny in pts:
                x, y = self._position_to_canvas(nx, ny, w, h)
                coords.extend([x, y])

            line_colour = vw.colour_settings.line_colour
            point_colour = vw.colour_settings.point_colour
            line_width = self._wand_visualiser_settings.trail.line_width
            point_radius = self._wand_visualiser_settings.trail.point_radius

            if n >= 2:
                if vw.line_id is None:
                    vw.line_id = self._canvas.create_line(
                        *coords,
                        fill=line_colour,
                        width=line_width,
                        smooth=self._wand_visualiser_settings.trail.smooth,
                        splinesteps=12 if self._wand_visualiser_settings.trail.smooth else 1,
                    )
                else:
                    self._canvas.coords(vw.line_id, *coords)
                    self._canvas.itemconfig(
                        vw.line_id,
                        fill=line_colour,
                        width=line_width,
                        smooth=self._wand_visualiser_settings.trail.smooth,
                        splinesteps=12 if self._wand_visualiser_settings.trail.smooth else 1,
                    )
            else:
                if vw.line_id is not None:
                    self._canvas.delete(vw.line_id)
                    vw.line_id = None

            if self._wand_visualiser_settings.trail.draw_points:
                r = point_radius
                it = iter(coords)
                for x, y in zip(it, it):
                    vw.dot_ids.append(
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

        if cm is CoordinateMode.UNIT:
            if self._wand_visualiser_settings.trail.clip_to_bounds:
                nx = max(0.0, min(1.0, nx))
                ny = max(0.0, min(1.0, ny))
            m = max(0, self._wand_visualiser_settings.trail.pixel_margin)
            w_eff = max(1, w - 2 * m)
            h_eff = max(1, h - 2 * m)

            x = nx * (w_eff - 1) + m
            y = ((1.0 - ny) if self._wand_visualiser_settings.trail.y_up else ny) * (h_eff - 1) + m
            return x, y

        raise ValueError(f"Unknown coords_mode: '{cm}'")

    def _sync_visualised_wands(self) -> None:
        current_ids = {w.id.upper(): w for w in self._tracked_wand_manager.tracked_wands()}

        # Remove missing (disconnected)
        for wand_id in list(self._visualised_wands.keys()):
            if wand_id not in current_ids:
                vw = self._visualised_wands.pop(wand_id)
                vw.dispose()
                self._colour_assigner.reserve(wand_id)

        # Add new (connected)
        for wand_id, wand in current_ids.items():
            if wand_id in self._visualised_wands:
                continue

            colour = self._colour_assigner.acquire(wand_id)
            settings = TrailColourSettings(line_colour=colour, point_colour=colour)
            vw = self._visualised_wand_factory.create(settings, wand, self._canvas)
            vw.start()
            self._visualised_wands[wand_id] = vw
