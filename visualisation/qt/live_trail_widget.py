from __future__ import annotations

from collections import deque
from typing import Deque

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPaintEvent, QPen, QPolygonF, QRadialGradient
from PySide6.QtWidgets import QWidget

from visualisation.configuration.trail_settings import TrailSettings
from visualisation.qt.coord_mapper import map_trail_point

# Sub-points inserted between each original point when smoothing (Catmull-Rom).
_SMOOTH_SUBDIVISIONS = 8


class LiveTrailWidget(QWidget):
    """Continuously-scrolling view of the wand's recent motion (last N points)."""

    def __init__(self, settings: TrailSettings, background: str) -> None:
        super().__init__()
        self._settings = settings
        self._background = QColor(background)

        self._points: Deque[tuple[float, float]] = deque(maxlen=max(1, settings.max_points))
        self._x = 0.0
        self._y = 0.0

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
            mapped = _catmull_rom(mapped, _SMOOTH_SUBDIVISIONS)

        if len(mapped) >= 2:
            self._draw_trail(painter, mapped, s)

        if self._settings.draw_points and mapped:
            self._draw_tip_sparkle(painter, mapped[-1], s)

    def _draw_trail(self, painter: QPainter, mapped: list[QPointF], s: float) -> None:
        """Comet trail: segment-by-segment, the old tail fades + tapers toward the
        newest point, with an optional soft glow underlay. One flat polyline when
        fade is off."""
        colour = QColor(self._settings.line_colour)
        lw = self._settings.line_width

        def stroke(p0: QPointF, p1: QPointF, width: float, c: QColor) -> None:
            pen = QPen(c)
            pen.setWidthF(width)
            pen.setCosmetic(True)  # width in device px — constant under the render_scale zoom
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(p0, p1)

        if not self._settings.fade:
            if self._settings.glow:
                glow = QColor(colour)
                glow.setAlphaF(0.18)
                painter.setPen(self._pen(glow, lw + self._settings.glow_width))
                painter.drawPolyline(QPolygonF(mapped))
            painter.setPen(self._pen(colour, lw))
            painter.drawPolyline(QPolygonF(mapped))
            return

        n = len(mapped)
        tail_a = self._settings.tail_alpha
        gw = self._settings.glow_width
        head_colour = QColor(self._settings.head_colour) if self._settings.gradient else colour
        for i in range(1, n):
            t = i / (n - 1)  # 0 at oldest tail, 1 at newest head
            alpha = tail_a + (1.0 - tail_a) * (t ** 1.3)
            width = lw * (0.35 + 0.65 * t)  # taper: thin tail, full-width head
            seg_colour = _lerp_colour(colour, head_colour, t) if self._settings.gradient else colour
            p0, p1 = mapped[i - 1], mapped[i]
            if self._settings.glow:
                gc = QColor(seg_colour)
                gc.setAlphaF(alpha * 0.28)
                stroke(p0, p1, width + gw, gc)
            cc = QColor(seg_colour)
            cc.setAlphaF(alpha)
            stroke(p0, p1, width, cc)

    def _draw_tip_sparkle(self, painter: QPainter, head: QPointF, s: float) -> None:
        """Bright halo + white-hot core at the newest point — the wand tip."""
        colour = QColor(self._settings.head_colour if self._settings.gradient else self._settings.line_colour)
        halo_r = (self._settings.line_width * 2.4) / s
        core_r = (self._settings.point_radius * 1.6) / s

        if self._settings.glow:
            grad = QRadialGradient(head, halo_r)
            inner = QColor(colour)
            inner.setAlphaF(0.85)
            outer = QColor(colour)
            outer.setAlphaF(0.0)
            grad.setColorAt(0.0, inner)
            grad.setColorAt(1.0, outer)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(head, halo_r, halo_r)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(colour.lighter(150))  # white-hot tip
        painter.drawEllipse(head, core_r, core_r)

    def _pen(self, colour: QColor, width: float) -> QPen:
        pen = QPen(colour)
        pen.setWidthF(width)
        pen.setCosmetic(True)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        return pen

    def _draw_axes(self, painter: QPainter, w: int, h: int) -> None:
        pen = QPen(QColor("#3a3a3a"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(w // 2, 0, w // 2, h)
        painter.drawLine(0, h // 2, w, h // 2)


def _lerp_colour(a: QColor, b: QColor, t: float) -> QColor:
    return QColor.fromRgbF(
        a.redF() + (b.redF() - a.redF()) * t,
        a.greenF() + (b.greenF() - a.greenF()) * t,
        a.blueF() + (b.blueF() - a.blueF()) * t,
    )


def _catmull_rom(pts: list[QPointF], k: int) -> list[QPointF]:
    """Densify a polyline into a smooth Catmull-Rom curve passing through every point.
    `k` sub-points are inserted per original segment. Endpoints are duplicated so the
    curve starts/ends exactly on the first/last point."""
    ext = [pts[0], *pts, pts[-1]]
    out: list[QPointF] = [pts[0]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for j in range(1, k + 1):
            t = j / k
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                (2 * p1.x())
                + (-p0.x() + p2.x()) * t
                + (2 * p0.x() - 5 * p1.x() + 4 * p2.x() - p3.x()) * t2
                + (-p0.x() + 3 * p1.x() - 3 * p2.x() + p3.x()) * t3
            )
            y = 0.5 * (
                (2 * p1.y())
                + (-p0.y() + p2.y()) * t
                + (2 * p0.y() - 5 * p1.y() + 4 * p2.y() - p3.y()) * t2
                + (-p0.y() + 3 * p1.y() - 3 * p2.y() + p3.y()) * t3
            )
            out.append(QPointF(x, y))
    return out
