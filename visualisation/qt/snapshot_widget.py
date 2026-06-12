from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from spells.scoring.cast_attempt import CastAttempt
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.qt.coord_mapper import map_normalized_point
from visualisation.qt.quality_colours import REJECT_COLOUR, colour_for_score


class SnapshotWidget(QWidget):
    """Frozen view of the last qualifying cast attempt: shape overlay + scoring breakdown."""

    def __init__(self, settings: WandVisualiserSettings) -> None:
        super().__init__()
        self._settings = settings
        self._snapshot = settings.snapshot
        self._background = QColor(settings.window.panel_colour)
        self._text_colour = QColor(settings.window.text_colour)
        self._attempt: CastAttempt | None = None

    def set_attempt(self, attempt: CastAttempt) -> None:
        self._attempt = attempt
        self.update()

    def clear(self) -> None:
        self._attempt = None
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), self._background)

        w = max(self.width(), 1)
        h = max(self.height(), 1)

        if self._attempt is None:
            self._draw_placeholder(painter, w, h)
            return

        shape_h = int(h * 0.5)
        self._draw_shape(painter, self._attempt, QRectF(0, 0, w, shape_h))
        self._draw_breakdown(painter, self._attempt, QRectF(0, shape_h, w, h - shape_h))

    # ── shape overlay ───────────────────────────────────────────
    def _draw_shape(self, painter: QPainter, attempt: CastAttempt, rect: QRectF) -> None:
        painter.save()
        painter.setClipRect(rect)
        painter.translate(rect.topLeft())
        w = int(rect.width())
        h = int(rect.height())
        margin = 24

        # template (the "ideal" shape) underneath
        self._draw_path(painter, attempt.template_points, self._snapshot.template_colour, w, h, margin, width=2, dashed=True)
        # the player's normalised stroke on top
        self._draw_path(painter, attempt.normalized_points, self._snapshot.stroke_colour, w, h, margin, width=3)
        painter.restore()

    def _draw_path(
        self,
        painter: QPainter,
        points: tuple[tuple[float, float], ...],
        colour: str,
        w: int,
        h: int,
        margin: int,
        *,
        width: int,
        dashed: bool = False,
    ) -> None:
        if len(points) < 2:
            return
        mapped = [
            QPointF(*map_normalized_point(px, py, w, h, margin=margin, y_up=self._settings.trail.y_up))
            for px, py in points
        ]
        pen = QPen(QColor(colour))
        pen.setWidth(width)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawPolyline(QPolygonF(mapped))

    # ── scoring breakdown ───────────────────────────────────────
    def _draw_breakdown(self, painter: QPainter, attempt: CastAttempt, rect: QRectF) -> None:
        painter.save()
        painter.translate(rect.topLeft())
        score = attempt.score
        x = 14.0
        y = 22.0
        w = rect.width()

        # header: spell label + tier on the left, big quality-coloured total on the right
        quality_colour = colour_for_score(score)
        if not score.passed_gates:
            tier = "REJECTED"
        elif score.quality is not None:
            tier = score.quality.name + ("  [pity]" if score.pity_pass else "")
        else:
            tier = "UNRECOGNISED"

        header_font = QFont("Menlo")
        header_font.setPointSize(15)
        header_font.setBold(True)
        painter.setFont(header_font)
        painter.setPen(QColor(quality_colour))
        painter.drawText(QPointF(x, y), f"{score.label}  {tier}")

        total_font = QFont("Menlo")
        total_font.setPointSize(22)
        total_font.setBold(True)
        painter.setFont(total_font)
        total_text = f"{score.total:.0f}"
        total_w = painter.fontMetrics().horizontalAdvance(total_text)
        painter.drawText(QPointF(w - total_w - 16, y + 6), total_text)

        body = QFont("Menlo")
        body.setPointSize(10)
        painter.setFont(body)
        painter.setPen(self._text_colour)

        y += 30
        painter.drawText(QPointF(x, y), f"match {score.match_accuracy * 100:.1f}%   "
                                        f"dur {attempt.duration_s:.2f}s   "
                                        f"path {attempt.path_length:.2f}   samples {attempt.point_count}")

        # gate failures (only when rejected)
        if score.gate_failures:
            y += 18
            painter.setPen(QColor(REJECT_COLOUR))
            painter.drawText(QPointF(x, y), "gates: " + ", ".join(score.gate_failures))
            painter.setPen(self._text_colour)

        # component bars
        y += 26
        components = [
            ("base", score.base),
            ("xp", score.xp_bonus),
            ("cadence", score.cadence_bonus),
            ("tempo", score.tempo_bonus),
            ("streak", score.streak_bonus),
        ]
        bar_max = max(score.total, 120.0)
        bar_x = x + 70
        bar_w = w - bar_x - 60
        for name, value in components:
            self._draw_bar(painter, name, value, x, bar_x, y, bar_w, bar_max, "#60a5fa")
            y += 20

        # candidates (one per line)
        y += 18
        painter.setFont(body)
        painter.setPen(QColor("#9ca3af"))
        painter.drawText(QPointF(x, y), "candidates:")
        for c in attempt.candidates[:3]:
            y += 16
            painter.drawText(QPointF(x + 12, y), f"{c.label} {c.score * 100:.0f}%")
        painter.restore()

    def _draw_bar(
        self,
        painter: QPainter,
        name: str,
        value: float,
        label_x: float,
        bar_x: float,
        y: float,
        bar_w: float,
        bar_max: float,
        colour: str,
    ) -> None:
        painter.setPen(self._text_colour)
        painter.drawText(QPointF(label_x, y + 4), name)

        track = QRectF(bar_x, y - 8, bar_w, 12)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2b2b2b"))
        painter.drawRoundedRect(track, 3, 3)

        frac = 0.0 if bar_max <= 0 else max(0.0, min(1.0, value / bar_max))
        if frac > 0:
            fill = QRectF(bar_x, y - 8, bar_w * frac, 12)
            painter.setBrush(QColor(colour))
            painter.drawRoundedRect(fill, 3, 3)

        painter.setPen(self._text_colour)
        painter.drawText(QPointF(bar_x + bar_w + 6, y + 4), f"{value:.1f}")

    def _draw_placeholder(self, painter: QPainter, w: int, h: int) -> None:
        painter.setPen(QColor("#555"))
        font = QFont("Menlo")
        font.setPointSize(13)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "awaiting first spell cast…")
