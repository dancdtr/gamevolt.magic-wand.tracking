# tk_wand_trail_renderer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from coordinate_mode import CoordinateMode
from gamevolt.configuration.settings_base import SettingsBase
from input.wand_position_trail import WandPositionTrail
from preview import TkPreview


@dataclass
class TkWandTrailRendererSettings(SettingsBase):
    line_width: int = 2
    line_color: str = "#5eead4"
    draw_points: bool = False
    point_radius: int = 3
    point_colour: str | None = None
    smooth: bool = True
    coords_mode: CoordinateMode = CoordinateMode.CENTRED  # "centered" = [-1..1], origin at centre
    y_up: bool = True  # True => +Y up (top), False => screen down
    clip_to_bounds: bool = True  # clamp input coords into valid range
    pixel_margin: int = 0  # optional inner padding (pixels)


class TkWandTrailRenderer:
    def __init__(self, preview: TkPreview, trail: WandPositionTrail, settings: TkWandTrailRendererSettings) -> None:
        self._canvas = preview.canvas
        self._trail = trail
        self._s = settings

        self._line_id: int | None = None
        self._dot_ids: list[int] = []

        self._canvas.bind("<Configure>", lambda e: self.draw())

    def destroy(self) -> None:
        if self._line_id is not None:
            self._canvas.delete(self._line_id)
            self._line_id = None
        for i in self._dot_ids:
            self._canvas.delete(i)
        self._dot_ids.clear()

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
            x, y = self._to_canvas(nx, ny, w, h)
            coords.extend([x, y])

        if n >= 2:
            if self._line_id is None:
                self._line_id = self._canvas.create_line(
                    *coords,
                    fill=self._s.line_color,
                    width=self._s.line_width,
                    smooth=self._s.smooth,
                    splinesteps=12 if self._s.smooth else 1,
                )
            else:
                self._canvas.coords(self._line_id, *coords)
                self._canvas.itemconfig(
                    self._line_id,
                    fill=self._s.line_color,
                    width=self._s.line_width,
                    smooth=self._s.smooth,
                    splinesteps=12 if self._s.smooth else 1,
                )
        else:
            if self._line_id is not None:
                self._canvas.delete(self._line_id)
                self._line_id = None

        if self._s.draw_points:
            r = self._s.point_radius
            it = iter(coords)
            for x, y in zip(it, it):
                self._dot_ids.append(
                    self._canvas.create_oval(
                        x - r,
                        y - r,
                        x + r,
                        y + r,
                        fill=self._s.point_colour or self._s.line_color,
                        outline=self._s.point_colour or self._s.line_color,
                    )
                )

    # ── helpers ──────────────────────────────────────────────────────────────
    def _to_canvas(self, nx: float, ny: float, w: int, h: int) -> Tuple[float, float]:
        cm = self._s.coords_mode

        if cm is CoordinateMode.CENTRED:
            if self._s.clip_to_bounds:
                nx = max(-1.0, min(1.0, nx))
                ny = max(-1.0, min(1.0, ny))
            m = max(0, self._s.pixel_margin)
            w_eff = max(1, w - 2 * m)
            h_eff = max(1, h - 2 * m)

            x = ((nx + 1.0) * 0.5) * (w_eff - 1) + m
            y = ((1.0 - (ny + 1.0) * 0.5) if self._s.y_up else ((ny + 1.0) * 0.5)) * (h_eff - 1) + m
            return x, y

        elif cm is CoordinateMode.UNIT:
            if self._s.clip_to_bounds:
                nx = max(0.0, min(1.0, nx))
                ny = max(0.0, min(1.0, ny))
            m = max(0, self._s.pixel_margin)
            w_eff = max(1, w - 2 * m)
            h_eff = max(1, h - 2 * m)

            x = nx * (w_eff - 1) + m
            y = ((1.0 - ny) if self._s.y_up else ny) * (h_eff - 1) + m
            return x, y

        # Fallback: treat unknown mode as centred (or raise)
        # raise ValueError(f"Unknown coords_mode: {cm!r}")
        # Treat as CENTRED:
        if self._s.clip_to_bounds:
            nx = max(-1.0, min(1.0, nx))
            ny = max(-1.0, min(1.0, ny))
        m = max(0, self._s.pixel_margin)
        w_eff = max(1, w - 2 * m)
        h_eff = max(1, h - 2 * m)
        x = ((nx + 1.0) * 0.5) * (w_eff - 1) + m
        y = ((1.0 - (ny + 1.0) * 0.5) if self._s.y_up else ((ny + 1.0) * 0.5)) * (h_eff - 1) + m
        return x, y
