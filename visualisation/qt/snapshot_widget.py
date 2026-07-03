from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from spells.scoring.cast_attempt import CastAttempt
from spells.scoring.cast_score import CastScore
from spells.scoring.scoring_modifier import ScoringModifier
from spells.spell_cast_quality import SpellCastQuality
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.qt.coord_mapper import map_normalized_point
from visualisation.qt.quality_colours import REJECT_COLOUR, colour_for_score

_MAX_STARS = len(SpellCastQuality)  # quality tiers map 1:1 onto filled stars
_MUTED_COLOUR = "#8a8f98"       # matches SpellInfoCard muted grey
_DIM_STAR_COLOUR = "#3a3a3a"
_ACCENT = "#c9a227"             # gold rule — ties the pane to the left-hand card
_SERIF = "Georgia"             # serif display face, as on the card title
_MARGIN = 24.0


class SnapshotWidget(QWidget):
    """Frozen view of the last qualifying cast attempt: shape overlay + scoring breakdown.

    Spell lore lives in the left-pane `SpellInfoCard`, not here — this pane is scoring only."""

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

        self._draw_title(painter, w)
        title_h = 40

        if self._attempt is None:
            return

        shape_h = int(h * 0.40)
        self._draw_shape(painter, self._attempt, QRectF(_MARGIN, title_h, w - 2 * _MARGIN, shape_h - _MARGIN))
        self._draw_breakdown(painter, self._attempt, QRectF(0, title_h + shape_h, w, h - title_h - shape_h))

    def _draw_title(self, painter: QPainter, w: int) -> None:
        font = QFont(_SERIF)
        font.setPointSize(13)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(_MUTED_COLOUR))
        painter.drawText(QPointF(_MARGIN, 28), "LAST SPELL CAST")

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
        x = _MARGIN
        y = 34.0
        w = rect.width()
        right = w - _MARGIN

        # header: spell label + tier on the left, big quality-coloured total on the right
        quality_colour = colour_for_score(score)
        if not score.passed_gates:
            tier = "REJECTED"
        elif score.quality is not None:
            tier = score.quality.name + ("  ✦ pity" if score.pity_pass else "")
        else:
            tier = "FAILED"

        # serif label, matching the left-hand card title
        header_font = QFont(_SERIF)
        header_font.setPointSize(23)
        header_font.setBold(True)
        painter.setFont(header_font)
        painter.setPen(QColor(quality_colour))
        # Share the total's baseline so the name and the big number bottom-align.
        painter.drawText(QPointF(x, y + 16), score.label.upper())

        # big quality-coloured total, right-aligned, with a small "POINTS" caption
        total_font = QFont(_SERIF)
        total_font.setPointSize(40)
        total_font.setBold(True)
        painter.setFont(total_font)
        painter.setPen(QColor(quality_colour))
        total_text = f"{score.total:.0f}"
        total_w = painter.fontMetrics().horizontalAdvance(total_text)
        painter.drawText(QPointF(right - total_w, y + 16), total_text)
        caption = QFont("Menlo")
        caption.setPointSize(9)
        painter.setFont(caption)
        painter.setPen(QColor(_MUTED_COLOUR))
        pts_w = painter.fontMetrics().horizontalAdvance("POINTS")
        painter.drawText(QPointF(right - pts_w, y + 32), "POINTS")

        # gold divider rule under the header — ties this pane to the card
        rule_y = y + 44
        rule = QPen(QColor(_ACCENT))
        rule.setWidth(1)
        painter.setPen(rule)
        painter.drawLine(QPointF(x, rule_y), QPointF(right, rule_y))

        # star rating (quality out of _MAX_STARS), with the quality tier below it
        y = rule_y + 34
        self._draw_stars(painter, score, x, y, quality_colour)

        y += 26
        tier_font = QFont("Menlo")
        tier_font.setPointSize(11)
        tier_font.setBold(True)
        painter.setFont(tier_font)
        painter.setPen(QColor(quality_colour))
        painter.drawText(QPointF(x, y), tier)

        # gate failures (only when rejected)
        if score.gate_failures:
            y += 22
            painter.setPen(QColor(REJECT_COLOUR))
            painter.drawText(QPointF(x, y), "gates: " + ", ".join(score.gate_failures))
            painter.setPen(self._text_colour)

        # ── SCORING section ──────────────────────────────────
        y += 34
        self._draw_section_title(painter, "SCORING", x, y, right)

        y += 28
        # Each row: (label, value, modifier). A disabled modifier still shows its value
        # but is greyed out and excluded from the total. `base` has no modifier.
        components = [
            ("accuracy", score.base, None),
            ("xp bonus", score.xp_bonus, ScoringModifier.XP),
            ("cadence", score.cadence_bonus, ScoringModifier.CADENCE),
            ("tempo", score.tempo_bonus, ScoringModifier.TEMPO),
            ("pity bonus", score.streak_bonus, ScoringModifier.PITY),
        ]
        bar_max = max(score.total, 120.0)
        bar_x = x + 130
        bar_w = right - bar_x - 40
        for name, value, modifier in components:
            disabled = modifier is not None and modifier in score.disabled_modifiers
            self._draw_bar(painter, name, value, x, bar_x, y, bar_w, bar_max, quality_colour, disabled)
            y += 26

        # ── STATS section: stroke metrics ────────────────────
        y += 14
        self._draw_section_title(painter, "STATS", x, y, right)
        y += 24
        stats_font = QFont("Menlo")
        stats_font.setPointSize(11)
        painter.setFont(stats_font)
        painter.setPen(self._text_colour)
        painter.drawText(QPointF(x, y), f"dur {attempt.duration_s:.2f}s    "
                                        f"path {attempt.path_length:.2f}    "
                                        f"samples {attempt.point_count}")

        # candidates (one per line): label left, percentage right-aligned
        y += 28
        self._draw_section_title(painter, "CANDIDATES", x, y, right)
        cand_font = QFont("Menlo")
        cand_font.setPointSize(12)
        painter.setFont(cand_font)
        for c in attempt.candidates[:3]:
            y += 20
            painter.setPen(self._text_colour)
            painter.drawText(QPointF(x + 12, y), c.label)
            pct = f"{c.score * 100:.0f}%"
            painter.setPen(QColor(_MUTED_COLOUR))
            painter.drawText(QPointF(right - painter.fontMetrics().horizontalAdvance(pct), y), pct)
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

    def _draw_section_title(self, painter: QPainter, text: str, x: float, y: float, right: float) -> None:
        title_font = QFont("Menlo")
        title_font.setPointSize(11)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor(_MUTED_COLOUR))
        painter.drawText(QPointF(x, y), text)
        text_w = painter.fontMetrics().horizontalAdvance(text)
        rule_pen = QPen(QColor(_DIM_STAR_COLOUR))
        rule_pen.setWidth(1)
        painter.setPen(rule_pen)
        painter.drawLine(QPointF(x + text_w + 10, y - 4), QPointF(right, y - 4))

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
        disabled: bool = False,
    ) -> None:
        # A disabled modifier is drawn muted (label, fill + value) and tagged, but keeps its value.
        text_colour = QColor(_MUTED_COLOUR) if disabled else self._text_colour
        fill_colour = QColor(_MUTED_COLOUR) if disabled else QColor(colour)

        label_font = QFont("Menlo")
        label_font.setPointSize(12)
        painter.setFont(label_font)
        painter.setPen(text_colour)
        painter.drawText(QPointF(label_x, y + 5), name + (" (off)" if disabled else ""))

        track = QRectF(bar_x, y - 8, bar_w, 14)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2b2b2b"))
        painter.drawRoundedRect(track, 4, 4)

        frac = 0.0 if bar_max <= 0 else max(0.0, min(1.0, value / bar_max))
        if frac > 0:
            fill = QRectF(bar_x, y - 8, bar_w * frac, 14)
            painter.setBrush(fill_colour)
            painter.drawRoundedRect(fill, 4, 4)

        painter.setPen(text_colour)
        painter.drawText(QPointF(bar_x + bar_w + 8, y + 5), f"{value:.1f}")
