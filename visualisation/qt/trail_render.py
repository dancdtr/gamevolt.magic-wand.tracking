from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QRadialGradient

from visualisation.configuration.trail_settings import TrailSettings

# Sub-points inserted between each original point when smoothing (Catmull-Rom).
SMOOTH_SUBDIVISIONS = 8


def _pen(colour: QColor, width: float) -> QPen:
    pen = QPen(colour)
    pen.setWidthF(width)
    pen.setCosmetic(True)  # width in device px — constant under any painter scale
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    return pen


def draw_comet_trail(
    painter: QPainter,
    mapped: list[QPointF],
    settings: TrailSettings,
    *,
    colour: QColor,
    head_colour: QColor,
) -> None:
    """Comet trail: segment-by-segment, the old tail fades + tapers toward the
    newest point, with an optional soft glow underlay. One flat polyline when
    fade is off. `colour` is the tail/base colour, `head_colour` the gradient head."""
    from PySide6.QtGui import QPolygonF

    lw = settings.line_width

    def stroke(p0: QPointF, p1: QPointF, width: float, c: QColor) -> None:
        painter.setPen(_pen(c, width))
        painter.drawLine(p0, p1)

    if not settings.fade:
        if settings.glow:
            glow = QColor(colour)
            glow.setAlphaF(0.18)
            painter.setPen(_pen(glow, lw + settings.glow_width))
            painter.drawPolyline(QPolygonF(mapped))
        painter.setPen(_pen(colour, lw))
        painter.drawPolyline(QPolygonF(mapped))
        return

    n = len(mapped)
    tail_a = settings.tail_alpha
    gw = settings.glow_width
    head = head_colour if settings.gradient else colour
    for i in range(1, n):
        t = i / (n - 1)  # 0 at oldest tail, 1 at newest head
        alpha = tail_a + (1.0 - tail_a) * (t ** 1.3)
        width = lw * (0.35 + 0.65 * t)  # taper: thin tail, full-width head
        seg_colour = lerp_colour(colour, head, t) if settings.gradient else colour
        p0, p1 = mapped[i - 1], mapped[i]
        if settings.glow:
            gc = QColor(seg_colour)
            gc.setAlphaF(alpha * 0.28)
            stroke(p0, p1, width + gw, gc)
        cc = QColor(seg_colour)
        cc.setAlphaF(alpha)
        stroke(p0, p1, width, cc)


def draw_tip_sparkle(
    painter: QPainter,
    head: QPointF,
    settings: TrailSettings,
    *,
    colour: QColor,
    render_scale: float,
) -> None:
    """Bright halo + white-hot core at the newest point — the wand tip.
    `render_scale` is the painter zoom so radii stay constant in device pixels."""
    halo_r = (settings.line_width * 2.4) / render_scale
    core_r = (settings.point_radius * 1.6) / render_scale

    if settings.glow:
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


def lerp_colour(a: QColor, b: QColor, t: float) -> QColor:
    return QColor.fromRgbF(
        a.redF() + (b.redF() - a.redF()) * t,
        a.greenF() + (b.greenF() - a.greenF()) * t,
        a.blueF() + (b.blueF() - a.blueF()) * t,
    )


def catmull_rom(pts: list[QPointF], k: int) -> list[QPointF]:
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
