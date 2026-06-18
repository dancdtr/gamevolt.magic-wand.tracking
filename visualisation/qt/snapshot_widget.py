from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from spells.scoring.cast_attempt import CastAttempt
from spells.scoring.cast_score import CastScore
from spells.spell_cast_quality import SpellCastQuality
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.qt.coord_mapper import map_normalized_point
from visualisation.qt.quality_colours import REJECT_COLOUR, colour_for_score

_MAX_STARS = len(SpellCastQuality)  # quality tiers map 1:1 onto filled stars
_MUTED_COLOUR = "#6b7280"
_DIM_STAR_COLOUR = "#3a3a3a"


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

        shape_h = int(h * 0.45)
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
        # the player's normalised stroke on top, coloured by the cast's quality tier
        self._draw_path(painter, attempt.normalized_points, colour_for_score(attempt.score), w, h, margin, width=3)
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
        x = 18.0
        y = 30.0
        w = rect.width()

        # header: spell label + tier on the left, big quality-coloured total on the right
        quality_colour = colour_for_score(score)
        if not score.passed_gates:
            tier = "REJECTED"
        elif score.quality is not None:
            tier = score.quality.name + ("  ✦ pity" if score.pity_pass else "")
        else:
            tier = "FAILED"

        header_font = QFont("Menlo")
        header_font.setPointSize(19)
        header_font.setBold(True)
        painter.setFont(header_font)
        painter.setPen(QColor(quality_colour))
        painter.drawText(QPointF(x, y), score.label.upper())

        tier_font = QFont("Menlo")
        tier_font.setPointSize(12)
        tier_font.setBold(True)
        painter.setFont(tier_font)
        painter.drawText(QPointF(x, y + 22), tier)

        # big quality-coloured total, right-aligned, with a small "points" caption
        total_font = QFont("Menlo")
        total_font.setPointSize(40)
        total_font.setBold(True)
        painter.setFont(total_font)
        painter.setPen(QColor(quality_colour))
        total_text = f"{score.total:.0f}"
        total_w = painter.fontMetrics().horizontalAdvance(total_text)
        painter.drawText(QPointF(w - total_w - 18, y + 18), total_text)
        caption = QFont("Menlo")
        caption.setPointSize(10)
        painter.setFont(caption)
        painter.setPen(QColor(_MUTED_COLOUR))
        pts_w = painter.fontMetrics().horizontalAdvance("points")
        painter.drawText(QPointF(w - pts_w - 18, y + 34), "points")

        # star rating (quality out of _MAX_STARS)
        y += 50
        self._draw_stars(painter, score, x, y, quality_colour)

        # one-line stroke metrics
        y += 30
        metrics_font = QFont("Menlo")
        metrics_font.setPointSize(12)
        painter.setFont(metrics_font)
        painter.setPen(self._text_colour)
        painter.drawText(QPointF(x, y), f"match {score.match_accuracy * 100:.1f}%    "
                                        f"dur {attempt.duration_s:.2f}s    "
                                        f"path {attempt.path_length:.2f}    samples {attempt.point_count}")

        # gate failures (only when rejected)
        if score.gate_failures:
            y += 22
            painter.setPen(QColor(REJECT_COLOUR))
            painter.drawText(QPointF(x, y), "gates: " + ", ".join(score.gate_failures))
            painter.setPen(self._text_colour)

        # ── SCORING section ──────────────────────────────────
        y += 34
        self._draw_section_title(painter, "SCORING", x, y, w)

        y += 28
        components = [
            ("base", score.base),
            ("xp bonus", score.xp_bonus),
            ("cadence", score.cadence_bonus),
            ("tempo", score.tempo_bonus),
            ("failure bonus", score.streak_bonus),
        ]
        bar_max = max(score.total, 120.0)
        bar_x = x + 130
        bar_w = w - bar_x - 64
        for name, value in components:
            self._draw_bar(painter, name, value, x, bar_x, y, bar_w, bar_max, quality_colour)
            y += 26

        # candidates (one per line)
        y += 14
        self._draw_section_title(painter, "CANDIDATES", x, y, w)
        cand_font = QFont("Menlo")
        cand_font.setPointSize(12)
        painter.setFont(cand_font)
        painter.setPen(QColor("#9ca3af"))
        for c in attempt.candidates[:3]:
            y += 20
            painter.drawText(QPointF(x + 12, y), f"{c.label}  {c.score * 100:.0f}%")
        painter.restore()

    def _draw_stars(self, painter: QPainter, score: CastScore, x: float, y: float, colour: str) -> None:
        filled = self._star_count(score)
        star_font = QFont()
        star_font.setPointSize(26)
        painter.setFont(star_font)
        step = painter.fontMetrics().horizontalAdvance("★") + 4
        for i in range(_MAX_STARS):
            if i < filled:
                painter.setPen(QColor(colour))
                glyph = "★"
            else:
                painter.setPen(QColor(_DIM_STAR_COLOUR))
                glyph = "☆"
            painter.drawText(QPointF(x + i * step, y), glyph)

    @staticmethod
    def _star_count(score: CastScore) -> int:
        if not score.passed_gates or score.quality is None:
            return 0
        return list(SpellCastQuality).index(score.quality) + 1

    def _draw_section_title(self, painter: QPainter, text: str, x: float, y: float, w: float) -> None:
        title_font = QFont("Menlo")
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor(_MUTED_COLOUR))
        painter.drawText(QPointF(x, y), text)
        text_w = painter.fontMetrics().horizontalAdvance(text)
        rule_pen = QPen(QColor(_DIM_STAR_COLOUR))
        rule_pen.setWidth(1)
        painter.setPen(rule_pen)
        painter.drawLine(QPointF(x + text_w + 10, y - 4), QPointF(w - 18, y - 4))

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
        label_font = QFont("Menlo")
        label_font.setPointSize(12)
        painter.setFont(label_font)
        painter.setPen(self._text_colour)
        painter.drawText(QPointF(label_x, y + 5), name)

        track = QRectF(bar_x, y - 8, bar_w, 14)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2b2b2b"))
        painter.drawRoundedRect(track, 4, 4)

        frac = 0.0 if bar_max <= 0 else max(0.0, min(1.0, value / bar_max))
        if frac > 0:
            fill = QRectF(bar_x, y - 8, bar_w * frac, 14)
            painter.setBrush(QColor(colour))
            painter.drawRoundedRect(fill, 4, 4)

        painter.setPen(self._text_colour)
        painter.drawText(QPointF(bar_x + bar_w + 8, y + 5), f"{value:.1f}")

    def _draw_placeholder(self, painter: QPainter, w: int, h: int) -> None:
        painter.setPen(QColor("#555"))
        font = QFont("Menlo")
        font.setPointSize(16)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "awaiting first spell cast…")
