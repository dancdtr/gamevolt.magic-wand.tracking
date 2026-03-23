from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Callable, Iterable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from wand.wand_rotation_raw import WandRotationRaw


class WandClient:
    def __init__(
        self,
        logger: Logger,
        id: str,
        disconnect_after_s: float = 2.0,
    ) -> None:
        self._logger = logger
        self._id = id.upper()
        self._disconnect_after_s = float(disconnect_after_s)

        self._last_seen_monotonic: float | None = None
        self._last_seen_utc: datetime | None = None

        self.wand_rotation_raw_updated: Event[Callable[[WandRotationRaw], None]] = Event()

    @property
    def id(self) -> str:
        return self._id

    def touch(self, now_monotonic: float | None = None) -> None:
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

    def on_wand_rotation_data(self, t0_ms: int, sample_dt_us: int, data_str: str) -> None:
        self.touch()

        dt_ms = sample_dt_us / 1000.0

        for idx, (fx, fy, fz) in enumerate(self._parse_items(data_str)):
            ms = int(round(t0_ms + idx * dt_ms))
            msg = WandRotationRaw(
                id=self._id,
                fx=fx,
                fy=fy,
                fz=fz,
                ms=ms,
            )
            self._emit(msg)

    def _parse_items(self, s: str) -> Iterable[tuple[float, float, float]]:
        if not s:
            return

        for part in s.split(";"):
            part = part.strip().strip('"')
            if not part:
                continue

            toks = [t.strip() for t in part.split(",") if t.strip()]
            if len(toks) < 3:
                continue

            try:
                fx_q15 = int(toks[0])
                fy_q15 = int(toks[1])
                fz_q15 = int(toks[2])
            except ValueError:
                continue

            fx = self._q15_to_float(fx_q15)
            fy = self._q15_to_float(fy_q15)
            fz = self._q15_to_float(fz_q15)

            fx, fy, fz = self._normalize_vector(fx, fy, fz)

            yield (fx, fy, fz)

    @staticmethod
    def _q15_to_float(v: int) -> float:
        return max(-1.0, min(1.0, v / 32767.0))

    @staticmethod
    def _normalize_vector(fx: float, fy: float, fz: float) -> tuple[float, float, float]:
        mag = math.sqrt(fx * fx + fy * fy + fz * fz)
        if mag < 1e-6:
            return (0.0, 0.0, 0.0)
        return (fx / mag, fy / mag, fz / mag)

    def _emit(self, msg: WandRotationRaw) -> None:
        self.wand_rotation_raw_updated.invoke(msg)
        self._logger.trace(f"Wand ({self._id}) EMIT @ {msg.ms} ms  fx={msg.fx:.4f}  fy={msg.fy:.4f}  fz={msg.fz:.4f}")
