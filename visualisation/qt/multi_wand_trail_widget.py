from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from visualisation.configuration.trail_settings import TrailSettings
from visualisation.qt.coord_mapper import map_trail_point
from visualisation.qt.trail_render import (
    SMOOTH_SUBDIVISIONS,
    catmull_rom,
    draw_comet_trail,
    draw_tip_sparkle,
)


@dataclass
class _WandTrail:
    colour: QColor
    head_colour: QColor
    x: float = 0.0
    y: float = 0.0
    points: Deque[tuple[float, float]] = field(default_factory=deque)


class MultiWandTrailWidget(QWidget):
    """Every active wand's live trail overlaid on one shared canvas, keyed by colour.

    Each wand integrates its own delta stream from the origin, so all trails radiate from
    centre — they overlap, and colour is what tells them apart (there's no shared floor
    position in the IMU rotation stream). A trail is reset on the wand's per-stroke settle
    and removed when the wand leaves its zone."""

    def __init__(self, settings: TrailSettings, background: str) -> None:
        super().__init__()
        self._settings = settings
        self._background = QColor(background)
        self._trails: dict[str, _WandTrail] = {}
        # Persistent id -> colour, independent of trail lifecycle: a trail removed on
        # zone-exit (or rebuilt by a late sample) must keep the same palette colour so it
        # always matches the legend swatch.
        self._colours: dict[str, tuple[QColor, QColor]] = {}

    def _colour_pair(self, wand_id: str) -> tuple[QColor, QColor]:
        return self._colours.get(
            wand_id,
            (QColor(self._settings.line_colour), QColor(self._settings.head_colour)),
        )

    def _new_trail(self, colour: QColor, head_colour: QColor) -> _WandTrail:
        return _WandTrail(
            colour=colour,
            head_colour=head_colour,
            points=deque(maxlen=max(1, self._settings.max_points)),
        )

    def set_colour(self, wand_id: str, colour: str) -> None:
        """Register a wand's trail colour. Always overwrites, and recolours a live trail so
        the canvas and legend never diverge."""
        c = QColor(colour)
        self._colours[wand_id] = (c, c.lighter(150))
        trail = self._trails.get(wand_id)
        if trail is not None:
            trail.colour, trail.head_colour = c, c.lighter(150)

    def add_delta(self, wand_id: str, x_delta: float, y_delta: float) -> None:
        trail = self._trails.get(wand_id)
        if trail is None:
            trail = self._new_trail(*self._colour_pair(wand_id))
            self._trails[wand_id] = trail

        trail.x += x_delta
        trail.y += y_delta
        s = self._settings.scale
        trail.points.append((trail.x * s, trail.y * s))
        self.update()

    def reset(self, wand_id: str) -> None:
        """Clear a wand's accrued stroke (fired on settle) — keeps its colour slot."""
        trail = self._trails.get(wand_id)
        if trail is None:
            return
        trail.x = 0.0
        trail.y = 0.0
        trail.points.clear()
        self.update()

    def remove(self, wand_id: str) -> None:
        """Drop the wand entirely (left its zone / went inactive)."""
        if self._trails.pop(wand_id, None) is not None:
            self.update()

    def clear_all(self) -> None:
        self._trails.clear()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), self._background)

        w = max(self.width(), 1)
        h = max(self.height(), 1)
        self._draw_axes(painter, w, h)

        # Draw-only zoom about the widget centre: magnifies rendered trails without
        # touching the data, mapping, or IMU. Shared by every wand.
        s = self._settings.render_scale
        if s != 1.0:
            painter.translate(w / 2.0, h / 2.0)
            painter.scale(s, s)
            painter.translate(-w / 2.0, -h / 2.0)

        for trail in self._trails.values():
            self._draw_one(painter, trail, w, h, s)

    def _draw_one(self, painter: QPainter, trail: _WandTrail, w: int, h: int, s: float) -> None:
        pts = list(trail.points)
        if not pts:
            return

        mapped = [
            QPointF(*map_trail_point(
                nx, ny, w, h,
                coords_mode=self._settings.coords_mode,
                y_up=self._settings.y_up,
                clip=self._settings.clip_to_bounds,
                margin=self._settings.pixel_margin,
            ))
            for nx, ny in pts
        ]

        if self._settings.smooth and len(mapped) >= 3:
            mapped = catmull_rom(mapped, SMOOTH_SUBDIVISIONS)

        if len(mapped) >= 2:
            head = trail.head_colour if self._settings.gradient else trail.colour
            draw_comet_trail(painter, mapped, self._settings, colour=trail.colour, head_colour=head)

        if self._settings.draw_points and mapped:
            tip = trail.head_colour if self._settings.gradient else trail.colour
            draw_tip_sparkle(painter, mapped[-1], self._settings, colour=tip, render_scale=s)

    def _draw_axes(self, painter: QPainter, w: int, h: int) -> None:
        pen = QPen(QColor("#3a3a3a"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(w // 2, 0, w // 2, h)
        painter.drawLine(0, h // 2, w, h // 2)
