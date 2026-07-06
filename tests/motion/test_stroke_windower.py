from __future__ import annotations

from motion.motion_phase_type import MotionPhaseType
from motion.stroke.configuration.stroke_windower_settings import StrokeWindowerSettings
from motion.stroke.stroke_windower import Stroke, StrokeWindower, join_strokes
from wand.wand_rotation import WandRotation


def _rotation(ts_ms: int, dx: float = 1.0, dy: float = 0.0) -> WandRotation:
    return WandRotation(id="W", ts_ms=ts_ms, x_delta=dx, y_delta=dy, nx=None, ny=None)


def _windower(min_points: int = 3, max_open_duration_s: float = 0.0) -> StrokeWindower:
    return StrokeWindower(StrokeWindowerSettings(min_points=min_points, max_open_duration_s=max_open_duration_s))


def _feed(windower: StrokeWindower, count: int, start_ms: int = 0, step_ms: int = 10) -> None:
    for i in range(count):
        windower.on_rotation(_rotation(start_ms + i * step_ms))


def test_holding_closes_stroke() -> None:
    windower = _windower()
    completed: list[Stroke] = []
    windower.stroke_completed.subscribe(completed.append)

    windower.on_phase(MotionPhaseType.MOVING)
    _feed(windower, 5)
    windower.on_phase(MotionPhaseType.HOLDING)

    assert len(completed) == 1
    assert completed[0].point_count == 5


def test_paused_emits_provisional_and_stroke_rides_on() -> None:
    windower = _windower()
    completed: list[Stroke] = []
    paused: list[Stroke] = []
    windower.stroke_completed.subscribe(completed.append)
    windower.stroke_paused.subscribe(paused.append)

    windower.on_phase(MotionPhaseType.MOVING)
    _feed(windower, 4)
    windower.on_phase(MotionPhaseType.PAUSED)

    assert len(paused) == 1
    assert paused[0].point_count == 4
    assert not completed

    # Motion resumes through the corner; the same stroke keeps accumulating.
    windower.on_phase(MotionPhaseType.MOVING)
    _feed(windower, 4, start_ms=100)
    windower.on_phase(MotionPhaseType.HOLDING)

    assert len(completed) == 1
    assert completed[0].point_count == 8


def test_paused_below_min_points_emits_nothing() -> None:
    windower = _windower(min_points=5)
    paused: list[Stroke] = []
    windower.stroke_paused.subscribe(paused.append)

    windower.on_phase(MotionPhaseType.MOVING)
    _feed(windower, 3)
    windower.on_phase(MotionPhaseType.PAUSED)

    assert not paused


def test_abort_open_stroke_suppresses_completion() -> None:
    windower = _windower()
    completed: list[Stroke] = []
    windower.stroke_completed.subscribe(completed.append)

    windower.on_phase(MotionPhaseType.MOVING)
    _feed(windower, 6)
    windower.abort_open_stroke()
    windower.on_phase(MotionPhaseType.HOLDING)

    assert not completed


def test_short_stroke_dropped_at_finish() -> None:
    windower = _windower(min_points=8)
    completed: list[Stroke] = []
    windower.stroke_completed.subscribe(completed.append)

    windower.on_phase(MotionPhaseType.MOVING)
    _feed(windower, 4)
    windower.on_phase(MotionPhaseType.HOLDING)

    assert not completed


def test_trailing_cap_drops_old_points() -> None:
    windower = _windower(min_points=3, max_open_duration_s=1.0)
    completed: list[Stroke] = []
    windower.stroke_completed.subscribe(completed.append)

    windower.on_phase(MotionPhaseType.MOVING)
    # 3s of samples at 100ms spacing; only the trailing ~1s survives.
    _feed(windower, 31, step_ms=100)
    windower.on_phase(MotionPhaseType.HOLDING)

    assert len(completed) == 1
    stroke = completed[0]
    assert stroke.point_count <= 11
    assert stroke.end_ts_ms - stroke.start_ts_ms <= 1000


def test_join_strokes_concatenates_and_recomputes_length() -> None:
    a = Stroke(points=[(0.0, 0.0), (1.0, 0.0)], times_ms=[0, 10], path_length=1.0)
    b = Stroke(points=[(2.0, 0.0), (3.0, 0.0)], times_ms=[200, 210], path_length=1.0)

    joined = join_strokes([a, b])

    assert joined.points == [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)]
    assert joined.times_ms == [0, 10, 200, 210]
    # Includes the 1-unit bridge across the pause gap.
    assert joined.path_length == 3.0
