from __future__ import annotations

from motion.stroke.stroke_windower import Stroke
from spells.matching.dollar_one.dollar_one_recognizer import Recognition
from spells.scoring.cast_score import CastScore
from spells.spell_cast_quality import SpellCastQuality
from wand.cast_assembler import CastAssembler, CastEvaluation
from wand.configuration.cast_assembly_settings import CastAssemblySettings


class _NullLogger:
    def debug(self, *_args, **_kwargs) -> None: ...
    def info(self, *_args, **_kwargs) -> None: ...
    def verbose(self, *_args, **_kwargs) -> None: ...
    def warning(self, *_args, **_kwargs) -> None: ...
    def error(self, *_args, **_kwargs) -> None: ...


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _stroke(point_count: int, start_ms: int = 0) -> Stroke:
    points = [(float(i), 0.0) for i in range(point_count)]
    times = [start_ms + i * 10 for i in range(point_count)]
    return Stroke(points=points, times_ms=times, path_length=float(point_count - 1))


def _cast(recognized: bool, accuracy: float) -> CastScore:
    return CastScore(
        label="LUMOS",
        match_accuracy=accuracy,
        base=accuracy * 100.0,
        xp_bonus=0.0,
        cadence_bonus=0.0,
        tempo_bonus=0.0,
        streak_bonus=0.0,
        difficulty_weight=1.0,
        total=accuracy * 100.0,
        quality=SpellCastQuality.RUDIMENTARY if recognized else None,
        passed_gates=recognized,
        gate_failures=() if recognized else ("accuracy<0.40",),
    )


def _evaluate_by_point_count(min_points_to_pass: int, accuracy: float = 0.8):
    """Fake evaluator: a candidate 'matches' once it carries enough points — a stand-in
    for 'the full glyph is present'. Records every candidate it sees."""
    seen: list[int] = []

    def evaluate(stroke: Stroke) -> CastEvaluation | None:
        seen.append(stroke.point_count)
        recognized = stroke.point_count >= min_points_to_pass
        return CastEvaluation(
            stroke=stroke,
            results=[Recognition("LUMOS", accuracy)],
            cast=_cast(recognized, accuracy if recognized else accuracy / 2),
        )

    evaluate.seen = seen  # type: ignore[attr-defined]
    return evaluate


def _assembler(evaluate, clock: _Clock | None = None, **overrides) -> CastAssembler:
    settings = CastAssemblySettings(**overrides)
    return CastAssembler(_NullLogger(), settings, evaluate, now=clock or _Clock())


def test_recognised_segment_commits_immediately() -> None:
    assembler = _assembler(_evaluate_by_point_count(10))
    committed: list[CastEvaluation] = []
    rejected: list[CastEvaluation] = []
    assembler.committed.subscribe(committed.append)
    assembler.rejected.subscribe(rejected.append)

    assembler.on_segment(_stroke(12))
    assembler.on_stopped()

    assert len(committed) == 1
    assert not rejected


def test_corner_pause_segments_merge_and_commit() -> None:
    # Neither half of the glyph passes alone; joined they do.
    evaluate = _evaluate_by_point_count(20)
    assembler = _assembler(evaluate)
    committed: list[CastEvaluation] = []
    assembler.committed.subscribe(committed.append)

    assembler.on_segment(_stroke(12, start_ms=0))
    assert not committed

    assembler.on_segment(_stroke(12, start_ms=500))
    assert len(committed) == 1
    assert committed[0].stroke.point_count == 24


def test_provisional_commits_only_past_soft_accuracy_bar() -> None:
    weak = _assembler(_evaluate_by_point_count(10, accuracy=0.5), soft_commit_accuracy=0.6)
    assert weak.on_provisional(_stroke(12)) is False

    strong = _assembler(_evaluate_by_point_count(10, accuracy=0.7), soft_commit_accuracy=0.6)
    committed: list[CastEvaluation] = []
    strong.committed.subscribe(committed.append)
    assert strong.on_provisional(_stroke(12)) is True
    assert len(committed) == 1


def test_stopped_resolves_pending_as_single_miscast() -> None:
    assembler = _assembler(_evaluate_by_point_count(100))
    rejected: list[CastEvaluation] = []
    assembler.rejected.subscribe(rejected.append)

    assembler.on_segment(_stroke(12, start_ms=0))
    assembler.on_segment(_stroke(12, start_ms=500))
    assert not rejected

    assembler.on_stopped()
    assert len(rejected) == 1

    # Buffer is spent: a second settle emits nothing more.
    assembler.on_stopped()
    assert len(rejected) == 1


def test_post_commit_trailing_motion_suppressed() -> None:
    clock = _Clock()
    assembler = _assembler(_evaluate_by_point_count(10), clock=clock, post_commit_suppression_s=1.5)
    rejected: list[CastEvaluation] = []
    assembler.rejected.subscribe(rejected.append)

    clock.t = 0.0
    assembler.on_segment(_stroke(12))  # commits

    # Trailing junk (too few points to match) settles shortly after the cast.
    clock.t = 1.0
    assembler.on_segment(_stroke(8, start_ms=1000))
    assembler.on_stopped()
    assert not rejected

    # The same junk outside the suppression window is a real miscast.
    clock.t = 10.0
    assembler.on_segment(_stroke(8, start_ms=10_000))
    clock.t = 11.0
    assembler.on_stopped()
    assert len(rejected) == 1


def test_commit_clears_buffer() -> None:
    evaluate = _evaluate_by_point_count(10)
    assembler = _assembler(evaluate)

    assembler.on_segment(_stroke(12, start_ms=0))  # commits
    evaluate.seen.clear()  # type: ignore[attr-defined]

    assembler.on_segment(_stroke(12, start_ms=500))
    # Only the new segment is evaluated — nothing joined with the committed one.
    assert evaluate.seen == [12]  # type: ignore[attr-defined]


def test_stale_segments_pruned_from_joins() -> None:
    evaluate = _evaluate_by_point_count(100)
    assembler = _assembler(evaluate, max_segment_age_s=2.0)

    assembler.on_segment(_stroke(12, start_ms=0))
    evaluate.seen.clear()  # type: ignore[attr-defined]

    # 10s later: the old segment can't belong to this cast any more.
    assembler.on_segment(_stroke(12, start_ms=10_000))
    assert evaluate.seen == [12]  # type: ignore[attr-defined]
