from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import IO

from gamevolt.events.event import Event
from gamevolt.io import runtime_root
from recording.cast_image_renderer import CastImageRenderer
from recording.configuration.session_recorder_settings import SessionRecorderSettings
from spells.scoring.cast_attempt import CastAttempt
from spells.scoring.cast_score import CastScore
from wand.wand_rotation import WandRotation

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitise(name: str) -> str:
    cleaned = _UNSAFE.sub("_", name.strip()).strip("_")
    return cleaned or "session"


class SessionRecorder:
    """Captures a recording session to disk, driven by the visualiser's record toggle.

    On record-on it opens `<output_dir>/<timestamp>_<name>/` and, while active, writes:
      - `casts.jsonl`  one line per *recognised* cast (spell, quality, full score breakdown,
                       and the raw/normalised/template stroke points)
      - `raw.jsonl`    every wand rotation sample, for later analysis / trail rebuild
      - `images/`      a rendered snapshot PNG per cast (if an image renderer is supplied)
    On record-off it writes `session.json` (metadata + counts) and closes the files.
    """

    def __init__(
        self,
        logger: Logger,
        settings: SessionRecorderSettings,
        record_session_changed: Event[Callable[[bool, str], None]],
        cast_attempted: Event[Callable[[CastAttempt], None]],
        wand_rotation_updated: Event[Callable[[WandRotation], None]],
        min_match_accuracy: float,
        total_spells: int,
        image_renderer: CastImageRenderer | None = None,
    ) -> None:
        self._logger = logger
        self._settings = settings
        self._record_session_changed = record_session_changed
        self._cast_attempted = cast_attempted
        self._wand_rotation_updated = wand_rotation_updated
        self._min_match_accuracy = min_match_accuracy
        self._total_spells = total_spells
        self._image_renderer = image_renderer

        self._session_dir: Path | None = None
        self._casts_file: IO[str] | None = None
        self._raw_file: IO[str] | None = None
        self._name = ""
        self._started_at: datetime | None = None
        self._cast_count = 0
        self._sample_count = 0
        self._cast_summaries: list[dict] = []

    def start(self) -> None:
        self._record_session_changed.subscribe(self._on_record_changed)

    def stop(self) -> None:
        self._record_session_changed.unsubscribe(self._on_record_changed)
        if self._is_recording:
            self._end_session()

    @property
    def _is_recording(self) -> bool:
        return self._session_dir is not None

    def _on_record_changed(self, active: bool, name: str) -> None:
        if active and not self._is_recording:
            self._begin_session(name)
        elif not active and self._is_recording:
            self._end_session()

    def _begin_session(self, name: str) -> None:
        if not self._settings.is_enabled:
            self._logger.info("Session recorder disabled; ignoring record request.")
            return

        self._started_at = datetime.now()
        stamp = self._started_at.strftime("%Y%m%d-%H%M%S")
        base = self._resolve_output_dir()
        self._session_dir = base / f"{stamp}_{_sanitise(name)}"
        (self._session_dir / "images").mkdir(parents=True, exist_ok=True)

        self._casts_file = (self._session_dir / "casts.jsonl").open("w", encoding="utf-8")
        self._raw_file = (self._session_dir / "raw.jsonl").open("w", encoding="utf-8")
        self._name = name
        self._cast_count = 0
        self._sample_count = 0
        self._cast_summaries = []

        self._cast_attempted.subscribe(self._on_cast_attempted)
        self._wand_rotation_updated.subscribe(self._on_rotation)
        self._logger.info(f"Recording session '{name}' -> {self._session_dir}")

    def _end_session(self) -> None:
        self._cast_attempted.unsubscribe(self._on_cast_attempted)
        self._wand_rotation_updated.unsubscribe(self._on_rotation)

        session_dir = self._session_dir
        assert session_dir is not None  # guarded by _is_recording

        ended_at = datetime.now()
        meta = {
            "name": self._name,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "ended_at": ended_at.isoformat(),
            "cast_count": self._cast_count,
            "sample_count": self._sample_count,
            "metrics": _compute_metrics(self._cast_summaries, self._total_spells),
        }
        (session_dir / "session.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        for f in (self._casts_file, self._raw_file):
            if f is not None:
                f.close()

        self._logger.info(
            f"Recording session '{self._name}' finished: "
            f"{self._cast_count} casts, {self._sample_count} samples -> {session_dir}"
        )

        self._session_dir = None
        self._casts_file = None
        self._raw_file = None
        self._started_at = None

    def _on_rotation(self, rotation: WandRotation) -> None:
        if self._raw_file is None:
            return
        self._sample_count += 1
        self._raw_file.write(
            json.dumps(
                {
                    "wand_id": rotation.id,
                    "ts_ms": rotation.ts_ms,
                    "x_delta": rotation.x_delta,
                    "y_delta": rotation.y_delta,
                    "nx": rotation.nx,
                    "ny": rotation.ny,
                }
            )
            + "\n"
        )

    def _on_cast_attempted(self, attempt: CastAttempt) -> None:
        # Record the same attempts the visualiser snapshot shows: recognised casts plus
        # rejected ones that clear the noise gate. Sub-threshold noise flicks are dropped.
        if not self._shows_in_snapshot(attempt) or self._casts_file is None or self._session_dir is None:
            return

        self._cast_count += 1
        now = datetime.now()
        stamp = now.strftime("%H%M%S-") + f"{now.microsecond // 1000:03d}"
        score = attempt.score
        quality = self._quality_label(score)
        image_name = self._render_image(attempt, self._cast_count, stamp, score.label, quality)

        record = {
            "index": self._cast_count,
            "recorded_at": now.isoformat(),
            "wand_id": attempt.wand_id,
            "spell": score.label,
            "quality": quality,
            "recognized": score.recognized,
            "passed_gates": score.passed_gates,
            "gate_failures": list(score.gate_failures),
            "duration_s": attempt.duration_s,
            "path_length": attempt.path_length,
            "point_count": attempt.point_count,
            "score": {
                "match_accuracy": score.match_accuracy,
                "base": score.base,
                "xp_bonus": score.xp_bonus,
                "cadence_bonus": score.cadence_bonus,
                "tempo_bonus": score.tempo_bonus,
                "streak_bonus": score.streak_bonus,
                "difficulty_weight": score.difficulty_weight,
                "total": score.total,
                "pity_pass": score.pity_pass,
            },
            "candidates": [{"label": c.label, "score": c.score} for c in attempt.candidates],
            "stroke_points": [list(p) for p in attempt.stroke_points],
            "normalized_points": [list(p) for p in attempt.normalized_points],
            "template_points": [list(p) for p in attempt.template_points],
            "image": image_name,
        }
        self._casts_file.write(json.dumps(record) + "\n")
        self._casts_file.flush()

        self._cast_summaries.append(
            {
                "index": self._cast_count,
                "spell": score.label,
                "quality": quality,
                "recognized": score.recognized,
                "total": score.total,
                "base": score.base,
                "match_accuracy": score.match_accuracy,
                "duration_s": attempt.duration_s,
                "recorded_at": now.isoformat(),
                "image": image_name,
            }
        )

    def _shows_in_snapshot(self, attempt: CastAttempt) -> bool:
        # Mirrors QtWandVisualiser._passes_threshold.
        score = attempt.score
        return score.passed_gates or score.match_accuracy >= self._min_match_accuracy

    @staticmethod
    def _quality_label(score: CastScore) -> str:
        if not score.passed_gates:
            return "REJECTED"
        return score.quality.name if score.quality is not None else "FAILED"

    def _render_image(
        self, attempt: CastAttempt, index: int, stamp: str, label: str, quality: str
    ) -> str | None:
        if self._image_renderer is None or not self._settings.save_images or self._session_dir is None:
            return None
        name = f"{index:03d}_{stamp}_{_sanitise(label)}_{_sanitise(quality)}.png"
        try:
            self._image_renderer.render(attempt, self._session_dir / "images" / name)
        except Exception:
            self._logger.exception(f"Failed to render cast image for '{label}'")
            return None
        return name

    def _resolve_output_dir(self) -> Path:
        configured = Path(self._settings.output_dir)
        return configured if configured.is_absolute() else runtime_root() / configured


def _round(value: float, digits: int = 4) -> float:
    return round(value, digits)


def _standout(cast: dict, **extra: float) -> dict:
    """Trim a cast summary to the fields worth surfacing for a standout (links back to the cast)."""
    return {
        "spell": cast["spell"],
        "quality": cast["quality"],
        "total": _round(cast["total"], 1),
        "match_accuracy": _round(cast["match_accuracy"]),
        "duration_s": _round(cast["duration_s"], 2),
        "recorded_at": cast["recorded_at"],
        "image": cast["image"],
        **{k: _round(v, 1) for k, v in extra.items()},
    }


def _longest_combo(casts: list[dict]) -> int:
    """Most consecutive recognised casts (in record order)."""
    best = run = 0
    for c in casts:
        run = run + 1 if c["recognized"] else 0
        best = max(best, run)
    return best


def _compute_metrics(casts: list[dict], total_spells: int) -> dict:
    """Aggregate gameplay metrics over the session's recorded casts."""
    if not casts:
        return {"total_casts": 0, "spells_attempted": {"attempted": 0, "total": total_spells}}

    recognized = [c for c in casts if c["recognized"]]

    # Per-spell rollup (attempts include rejected-but-shown; recognised is the success count).
    spells = sorted({c["spell"] for c in casts})
    per_spell: dict[str, dict] = {}
    for spell in spells:
        attempts = [c for c in casts if c["spell"] == spell]
        wins = [c for c in attempts if c["recognized"]]
        per_spell[spell] = {
            "attempts": len(attempts),
            "recognized": len(wins),
            "success_rate": _round(len(wins) / len(attempts)),
            "best_total": _round(max((c["total"] for c in wins), default=0.0), 1),
            "best_match": _round(max(c["match_accuracy"] for c in attempts)),
            "avg_match": _round(sum(c["match_accuracy"] for c in attempts) / len(attempts)),
        }

    attempts_by_spell = Counter(c["spell"] for c in casts)
    favourite_spell, favourite_attempts = attempts_by_spell.most_common(1)[0]

    # Trickiest: lowest success rate, tie-broken toward more attempts (stronger evidence).
    trickiest = min(spells, key=lambda s: (per_spell[s]["success_rate"], -per_spell[s]["attempts"]))

    highest_cast = max(recognized, key=lambda c: c["total"], default=None)
    best_match_cast = max(casts, key=lambda c: c["match_accuracy"])
    fastest_cast = min(recognized, key=lambda c: c["duration_s"], default=None)
    flashiest_cast = max(recognized, key=lambda c: c["total"] - c["base"], default=None)
    misses = [c for c in casts if not c["recognized"]]
    closest_miss = max(misses, key=lambda c: c["match_accuracy"], default=None)

    # Signature spell: best average match among spells actually practised (>= 2 attempts).
    practised = [s for s in spells if per_spell[s]["attempts"] >= 2]
    signature = max(practised, key=lambda s: per_spell[s]["avg_match"], default=None)

    return {
        "total_casts": len(casts),
        "recognized_count": len(recognized),
        "rejected_count": len(casts) - len(recognized),
        "success_rate": _round(len(recognized) / len(casts)),
        "longest_combo": _longest_combo(casts),
        "total_points": _round(sum(c["total"] for c in recognized), 1),
        "average_match_accuracy": _round(sum(c["match_accuracy"] for c in casts) / len(casts)),
        "quality_counts": dict(Counter(c["quality"] for c in casts)),
        "spell_variety": {
            "attempted": len(spells),  # distinct spells attempted (e.g. 11 of `total`)
            "recognized": len({c["spell"] for c in recognized}),
            "total": total_spells,  # spells loaded / castable
        },
        "favourite_spell": {"spell": favourite_spell, "attempts": favourite_attempts},
        "signature_spell": {"spell": signature, **per_spell[signature]} if signature is not None else None,
        "trickiest_spell": {"spell": trickiest, **per_spell[trickiest]},
        "highest_scoring_cast": _standout(highest_cast) if highest_cast is not None else None,
        "best_match": _standout(best_match_cast),
        "fastest_cast": _standout(fastest_cast) if fastest_cast is not None else None,
        "flashiest_cast": (
            _standout(flashiest_cast, bonus=flashiest_cast["total"] - flashiest_cast["base"])
            if flashiest_cast is not None
            else None
        ),
        "closest_miss": _standout(closest_miss) if closest_miss is not None else None,
        "per_spell": per_spell,
    }
