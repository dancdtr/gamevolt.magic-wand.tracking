from __future__ import annotations

from collections import deque
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


class LiveTrailWidget(QWidget):
    """Continuously-scrolling view of the wand's recent motion (last N points)."""

    def __init__(self, settings: TrailSettings, background: str) -> None:
        super().__init__()
        self._settings = settings
        self._background = QColor(background)

        self._points: Deque[tuple[float, float]] = deque(maxlen=max(1, settings.max_points))
        self._x = 0.0
        self._y = 0.0
        self._enabled = True

    def set_enabled(self, enabled: bool) -> None:
        """Toggle trail rendering. Points keep accruing while off so re-enabling resumes live."""
        self._enabled = enabled
        self.update()

    def add_delta(self, x_delta: float, y_delta: float) -> None:
        self._x += x_delta
        self._y += y_delta
        s = self._settings.scale
        self._points.append((self._x * s, self._y * s))
        self.update()

    def reset(self) -> None:
        self._x = 0.0
        self._y = 0.0
        self._points.clear()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), self._background)

        w = max(self.width(), 1)
        h = max(self.height(), 1)

        self._draw_axes(painter, w, h)

        if not self._enabled:
            return

        pts = list(self._points)
        if not pts:
            return

        # Draw-only zoom about the widget centre: magnifies the rendered trail
        # without touching the data, mapping, or IMU.
        s = self._settings.render_scale
        if s != 1.0:
            painter.translate(w / 2.0, h / 2.0)
            painter.scale(s, s)
            painter.translate(-w / 2.0, -h / 2.0)

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
            head_colour = QColor(self._settings.head_colour) if self._settings.gradient else QColor(self._settings.line_colour)
            draw_comet_trail(painter, mapped, self._settings, colour=QColor(self._settings.line_colour), head_colour=head_colour)

        if self._settings.draw_points and mapped:
            tip = QColor(self._settings.head_colour if self._settings.gradient else self._settings.line_colour)
            draw_tip_sparkle(painter, mapped[-1], self._settings, colour=tip, render_scale=s)

    def _draw_axes(self, painter: QPainter, w: int, h: int) -> None:
        pen = QPen(QColor("#3a3a3a"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(w // 2, 0, w // 2, h)
        painter.drawLine(0, h // 2, w, h // 2)
