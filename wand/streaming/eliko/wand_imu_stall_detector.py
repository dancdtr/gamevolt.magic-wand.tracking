from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Protocol

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from wand.streaming.eliko.configuration.wand_imu_stall_detector_settings import WandImuStallDetectorSettings


class _LineSource(Protocol):
    @property
    def line_received(self) -> Event[Callable[[str], None]]: ...


@dataclass
class _TagState:
    last_pr_at: float | None = None
    last_pr_uptime_ms: int | None = None
    last_battery_at: float | None = None
    last_battery_mv: int | None = None
    stalled: bool = field(default=False)


class WandImuStallDetector:
    """Detect the silent IMU stall: PR stops while the tag stays alive.

    Incident signature (6-7 July 2026): the tag keeps ranging and answering
    GDHR battery polls, but PR packets stop mid-run with no boot banner; a
    CMD0 off/on cycle is delivered and acked yet PR never resumes — a firmware
    hang below the command layer, recoverable only by power-cycling the wand.

    Watches the line stream for PR headers (tag + uptime tick) and takes
    battery readings (via `record_battery`, wired to
    `WandBatteryMonitor.battery_updated` by the builder) as proof-of-life.
    A tag is stalled when its last PR is older than `stall_after_s` while a
    fresh battery reading proves the tag alive. Fires `stall_changed(tag,
    stalled)` on both onset and recovery.

    Logs the tag's uptime tick at the last PR: stalls recurring at a
    repeatable uptime would point at a deterministic firmware bug (counter or
    buffer wrap) rather than marginal hardware.
    """

    _PR_PREFIX = "$PEKIO,PR,"

    def __init__(
        self,
        logger: Logger,
        line_source: _LineSource,
        tracked_wand_ids: Iterable[str],
        settings: WandImuStallDetectorSettings,
    ) -> None:
        self._logger = logger
        self._line_source = line_source
        self._settings = settings
        self._states = {self._normalise_tag(t): _TagState() for t in tracked_wand_ids}
        self._stall_changed: Event[Callable[[str, bool], None]] = Event()
        self._check_task: asyncio.Task[None] | None = None

    @property
    def stall_changed(self) -> Event[Callable[[str, bool], None]]:
        return self._stall_changed

    def start(self) -> None:
        self._line_source.line_received.subscribe(self._on_line)
        self._check_task = asyncio.create_task(self._check_loop())

    def stop(self) -> None:
        if self._check_task is not None:
            self._check_task.cancel()
            self._check_task = None
        self._line_source.line_received.unsubscribe(self._on_line)

    def record_battery(self, tag: str, millivolts: int, percent: float) -> None:
        """Proof-of-life. Signature matches `WandBatteryMonitor.battery_updated`
        so the builder can subscribe it directly; `percent` is unused.
        """
        state = self._states.get(self._normalise_tag(tag))
        if state is None:
            return
        state.last_battery_at = time.monotonic()
        state.last_battery_mv = millivolts

    def _on_line(self, line: str) -> None:
        if not line.startswith(self._PR_PREFIX):
            return
        fields = line.split(",")
        try:
            tag = self._normalise_tag(fields[4])
            uptime_ms = int(fields[6], 16)
        except (IndexError, ValueError):
            return

        state = self._states.get(tag)
        if state is None:
            return
        state.last_pr_at = time.monotonic()
        state.last_pr_uptime_ms = uptime_ms
        if state.stalled:
            state.stalled = False
            self._logger.info(f"Wand ({tag}) IMU recovered: PR resumed (uptime {uptime_ms / 1000:.1f}s).")
            self._stall_changed.invoke(tag, False)

    async def _check_loop(self) -> None:
        while True:
            await asyncio.sleep(self._settings.check_interval_s)
            now = time.monotonic()
            for tag, state in self._states.items():
                self._check_tag(tag, state, now)

    def _check_tag(self, tag: str, state: _TagState, now: float) -> None:
        if state.stalled or state.last_pr_at is None:
            return
        pr_gap = now - state.last_pr_at
        if pr_gap < self._settings.stall_after_s:
            return
        # Only a battery reading newer than the last PR — and still fresh —
        # proves the tag is alive-but-silent rather than off/out of range.
        if state.last_battery_at is None or state.last_battery_at <= state.last_pr_at:
            return
        if now - state.last_battery_at > self._settings.liveness_max_age_s:
            return

        state.stalled = True
        uptime = state.last_pr_uptime_ms or 0
        battery_age = now - state.last_battery_at
        self._logger.warning(
            f"Wand ({tag}) IMU stalled: no PR for {pr_gap:.0f}s but tag alive "
            f"(GDHR {state.last_battery_mv}mV {battery_age:.0f}s ago). "
            f"Uptime at last PR: {uptime / 1000:.1f}s. Power-cycle the wand to recover."
        )
        self._stall_changed.invoke(tag, True)

    @staticmethod
    def _normalise_tag(raw: str) -> str:
        s = raw.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        return s.upper()
