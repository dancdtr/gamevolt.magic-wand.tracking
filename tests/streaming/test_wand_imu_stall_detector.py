from __future__ import annotations

import logging
import time
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging._levels import register_custom_levels
from gamevolt.logging._logger import Logger
from wand.streaming.eliko.configuration.wand_imu_stall_detector_settings import WandImuStallDetectorSettings
from wand.streaming.eliko.wand_imu_stall_detector import WandImuStallDetector

TAG = "1DAD"
PR_LINE = "$PEKIO,PR,001,0x1D99,0x1DAD,003,0x000BBD87,0x398B2F1BB9A3"


def _logger() -> Logger:
    register_custom_levels()
    logging.setLoggerClass(Logger)
    log = logging.getLogger("test.wand_imu_stall_detector")
    log.setLevel(logging.ERROR)
    return log  # type: ignore[return-value]


class _FakeLineSource:
    def __init__(self) -> None:
        self._line_received: Event[Callable[[str], None]] = Event()

    @property
    def line_received(self) -> Event[Callable[[str], None]]:
        return self._line_received


def _detector(**settings_overrides) -> tuple[WandImuStallDetector, list[tuple[str, bool]]]:
    settings = WandImuStallDetectorSettings(**settings_overrides)
    detector = WandImuStallDetector(
        logger=_logger(),
        line_source=_FakeLineSource(),
        tracked_wand_ids=[TAG],
        settings=settings,
    )
    changes: list[tuple[str, bool]] = []
    detector.stall_changed.subscribe(lambda tag, stalled: changes.append((tag, stalled)))
    return detector, changes


def _age_last_pr(detector: WandImuStallDetector, seconds: float) -> None:
    state = detector._states[TAG]
    assert state.last_pr_at is not None
    state.last_pr_at -= seconds


def test_stall_flagged_when_pr_quiet_but_battery_answering() -> None:
    detector, changes = _detector(stall_after_s=10.0)
    detector._on_line(PR_LINE)
    _age_last_pr(detector, 30.0)
    detector.record_battery(TAG, 1390, 64.4)

    detector._check_tag(TAG, detector._states[TAG], time.monotonic())

    assert changes == [(TAG, True)]


def test_no_stall_without_proof_of_life() -> None:
    detector, changes = _detector(stall_after_s=10.0)
    detector._on_line(PR_LINE)
    _age_last_pr(detector, 30.0)
    # No battery reading since the last PR: could be off / out of range.

    detector._check_tag(TAG, detector._states[TAG], time.monotonic())

    assert changes == []


def test_no_stall_when_liveness_reading_stale() -> None:
    detector, changes = _detector(stall_after_s=10.0, liveness_max_age_s=150.0)
    detector._on_line(PR_LINE)
    _age_last_pr(detector, 400.0)
    detector.record_battery(TAG, 1390, 64.4)
    detector._states[TAG].last_battery_at -= 300.0  # type: ignore[operator]

    detector._check_tag(TAG, detector._states[TAG], time.monotonic())

    assert changes == []


def test_no_stall_while_pr_fresh() -> None:
    detector, changes = _detector(stall_after_s=10.0)
    detector._on_line(PR_LINE)
    detector.record_battery(TAG, 1390, 64.4)

    detector._check_tag(TAG, detector._states[TAG], time.monotonic())

    assert changes == []


def test_recovery_on_pr_resume() -> None:
    detector, changes = _detector(stall_after_s=10.0)
    detector._on_line(PR_LINE)
    _age_last_pr(detector, 30.0)
    detector.record_battery(TAG, 1390, 64.4)
    detector._check_tag(TAG, detector._states[TAG], time.monotonic())

    detector._on_line(PR_LINE)

    assert changes == [(TAG, True), (TAG, False)]
    assert detector._states[TAG].stalled is False


def test_ignores_untracked_and_non_pr_lines() -> None:
    detector, _ = _detector()
    detector._on_line("$PEKIO,PR,001,0x1D99,0x1DAE,003,0x000BBD87,0x398B2F1BB9A3")  # untracked tag
    detector._on_line("$PEKIO,AC,123,0x1DAD,GDHR,voltages,0x0000056E,OTA")
    detector._on_line("$PEKIO,PR,junk")
    detector._on_line("garbage")

    assert detector._states[TAG].last_pr_at is None


def test_uptime_recorded_from_pr_header() -> None:
    detector, _ = _detector()
    detector._on_line(PR_LINE)

    assert detector._states[TAG].last_pr_uptime_ms == 0x000BBD87
