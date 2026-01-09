from __future__ import annotations

import time
from datetime import datetime, timezone
from logging import Logger
from typing import Callable, Iterable

from gamevolt.events.event import Event
from wand.configuration.wand_server_settings import WandClientSettings
from wand.wand_rotation_raw import WandRotationRaw


class WandClient:
    """
    Per-wand client that:
    - tracks last-seen time (monotonic + utc) for connection status
    - parses DATA payload into WandRotationRaw messages
    - optionally resamples to target_hz
    """

    def __init__(
        self,
        logger: Logger,
        settings: WandClientSettings,
        id: str,
        disconnect_after_s: float = 2.0,
    ) -> None:
        self._logger = logger
        self._id = id.upper()
        self._disconnect_after_s = float(disconnect_after_s)

        # Resample settings
        target_hz = getattr(settings, "target_hz", None)
        self._delay_ms: float | None = None
        if target_hz and target_hz > 0:
            self._delay_ms = 1000.0 / float(target_hz)

        self._dt_ms = 1000.0 / float(settings.imu_hz)

        # Connection tracking
        self._last_seen_monotonic: float | None = None
        self._last_seen_utc: datetime | None = None

        # Resample state
        self._prev_msg: WandRotationRaw | None = None
        self._next_emit_ms: float | None = None

        self.wand_rotation_raw_updated: Event[Callable[[WandRotationRaw], None]] = Event()

    @property
    def id(self) -> str:
        return self._id

    def touch(self, now_monotonic: float | None = None) -> None:
        """Mark the client as having received data 'now'."""
        if now_monotonic is None:
            now_monotonic = time.monotonic()
        self._last_seen_monotonic = now_monotonic
        self._last_seen_utc = datetime.now(timezone.utc)

    def is_connected(self, now_monotonic: float | None = None) -> bool:
        if self._last_seen_monotonic is None:
            return False
        if now_monotonic is None:
            now_monotonic = time.monotonic()
        return (now_monotonic - self._last_seen_monotonic) < self._disconnect_after_s

    def seconds_since_seen(self, now_monotonic: float | None = None) -> float | None:
        if self._last_seen_monotonic is None:
            return None
        if now_monotonic is None:
            now_monotonic = time.monotonic()
        return now_monotonic - self._last_seen_monotonic

    @property
    def last_seen_utc(self) -> datetime | None:
        return self._last_seen_utc

    # ── data ingestion ───────────────────────────────────────────────────────

    def on_wand_rotation_data(self, t_base: int, data_str: str) -> None:
        """
        Called per DATA line batch.
        Updates connection timestamp, parses samples, emits (resampled) WandRotationRaw.
        """
        self.touch()

        idx = 0
        for y100, p100 in self._parse_items(data_str):
            ms = int(round(t_base + idx * self._dt_ms))
            msg = WandRotationRaw(
                id=self._id,
                yaw=y100 / 100.0,
                pitch=p100 / 100.0,
                ms=ms,
            )
            self._emit_maybe_resample(msg)
            idx += 1

    def _parse_items(self, s: str) -> Iterable[tuple[int, int]]:
        if not s:
            return
        for part in s.split(";"):
            part = part.strip().strip('"')
            if not part:
                continue
            toks = [t.strip() for t in part.split(",") if t.strip()]
            if len(toks) < 2:
                continue
            try:
                y100 = int(toks[0])
                p100 = int(toks[1])
            except ValueError:
                continue
            yield (y100, p100)

    # ── resampling + emit ────────────────────────────────────────────────────

    def _emit_maybe_resample(self, msg: WandRotationRaw) -> None:
        if self._delay_ms is None:
            self._emit(msg)
            return

        if self._next_emit_ms is None:
            self._emit(msg)
            self._next_emit_ms = msg.ms + self._delay_ms
            self._prev_msg = msg
            return

        while msg.ms >= self._next_emit_ms:
            if self._prev_msg is None:
                chosen = msg
            else:
                prev_diff = abs(self._next_emit_ms - self._prev_msg.ms)
                curr_diff = abs(msg.ms - self._next_emit_ms)
                chosen = msg if curr_diff <= prev_diff else self._prev_msg

            self._emit(chosen)
            self._next_emit_ms += self._delay_ms

        self._prev_msg = msg

    def _emit(self, msg: WandRotationRaw) -> None:
        self.wand_rotation_raw_updated.invoke(msg)
        self._logger.debug(f"[{self._id}] EMIT @ {msg.ms} ms  yaw={msg.yaw:.3f}  pitch={msg.pitch:.3f}")
