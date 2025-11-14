# wand_data_reader.py
from __future__ import annotations

import re
from dataclasses import dataclass
from logging import Logger
from typing import Callable, Iterable

from gamevolt.events.event import Event
from gamevolt.serial.serial_receiver import SerialReceiver
from input.wand.wand_data_reader_settings import WandDataReaderSettings


@dataclass
class WandDataMessage:
    id: str  # tag hex, e.g. "E001"
    yaw: float  # degrees
    pitch: float  # degrees
    ms: int  # synthesized per-sample timestamp (ms)


class WandDataReader:
    """
    Parses anchor output:
      PKT t_rx=... t_base=... tag=E001 seq=141 nsamp=12
      DATA seq=141 data=-1013,-271; -1013,-271; ...

    - Takes first two ints in each item as yaw100,pitch100 (centi-deg) → degrees.
    - Synthesizes per-sample timestamps: ms = t_base + i*(1000/imu_hz).
    - Optional resample to target_hz (default 30 Hz). Set target_hz=None/0 to emit all.
    """

    # Matches the PKT header line
    _PKT_RE = re.compile(
        r"^PKT\s+t_rx=(?P<t_rx>\d+)\s+t_base=(?P<t_base>\d+)\s+tag=(?P<tag>[0-9A-Fa-f]+)\s+seq=(?P<seq>\d+)\s+nsamp=(?P<nsamp>\d+)\s*$"
    )
    # Matches either DATA or DATA_RAW lines (be forgiving)
    _DATA_RE = re.compile(r'^(?:DATA|DATA_RAW)\s+seq=(?P<seq>\d+)\s+data="?(?P<data>.*)"?\s*$')

    def __init__(self, logger: Logger, settings: WandDataReaderSettings):
        self._logger = logger
        self._settings = settings

        self._serial = SerialReceiver(logger=logger, settings=settings.serial_receiver)

        # timing
        # self._imu_hz = float(imu_hz)
        self._dt_ms = 1000.0 / self._settings.imu_hz
        self._delay_ms = 1000.0 / self._settings.target_hz
        # self._target_hz = None if not target_hz or target_hz <= 0 else float(target_hz)
        # self._delay_ms = None if self._target_hz is None else 1000.0 / self._target_hz

        # resample state
        self._next_emit_ms: float | None = None
        self._prev_msg: WandDataMessage | None = None

        # pair DATA with PKT via seq
        self._pending_headers: dict[int, tuple[int, str, int]] = {}
        # (t_base_ms, tag_hex, nsamp)

        # event
        self.wand_position_updated: Event[Callable[[WandDataMessage], None]] = Event()

    # ── lifecycle ────────────────────────────────────────────────────────────
    async def start(self) -> None:
        await self._serial.start()
        self._serial.data_received.subscribe(self._on_line)

    async def stop(self) -> None:
        self._serial.data_received.unsubscribe(self._on_line)

        await self._serial.stop()
        self._pending_headers.clear()
        self._next_emit_ms = None
        self._prev_msg = None

    # ── internal parsing ─────────────────────────────────────────────────────
    def _on_line(self, line: str) -> None:
        if not line:
            return

        # PKT header
        m = self._PKT_RE.match(line)
        if m:
            seq = int(m["seq"])
            t_base = int(m["t_base"])
            tag_hex = m["tag"].upper()
            nsamp = int(m["nsamp"])
            self._pending_headers[seq] = (t_base, tag_hex, nsamp)
            return

        # DATA batch
        m = self._DATA_RE.match(line)
        if not m:
            return

        seq = int(m["seq"])
        data_str = m["data"].strip()

        # get header if present; otherwise synthesize something reasonable
        t_base, tag_hex, _ = self._pending_headers.pop(seq, (0, "????", 0))

        idx = 0
        for y100, p100 in self._parse_items(data_str):
            ms = int(round(t_base + idx * self._dt_ms))
            msg = WandDataMessage(
                id=tag_hex,
                yaw=y100 / 100.0,
                pitch=p100 / 100.0,
                ms=ms,
            )
            self._emit_maybe_resample(msg)
            idx += 1

    def _parse_items(self, s: str) -> Iterable[tuple[int, int]]:
        """
        Parse 'a,b; c,d; ...' → yield (a,b) as ints (first two numbers per item).
        Accepts extra numbers but ignores them (for robustness).
        """
        if not s:
            return
        # Split by ';'
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

    # ── resampling / emit ────────────────────────────────────────────────────
    def _emit_maybe_resample(self, msg: WandDataMessage) -> None:
        if self._delay_ms is None:
            self._emit(msg)
            return

        if self._next_emit_ms is None:
            self._emit(msg)
            self._next_emit_ms = msg.ms + self._delay_ms
            self._prev_msg = msg
            return

        # Emit at fixed cadence; pick whichever (prev/current) is closer to the cadence tick
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

    def _emit(self, msg: WandDataMessage) -> None:
        self.wand_position_updated.invoke(msg)
        self._logger.debug(f"EMIT @ {msg.ms} ms  yaw={msg.yaw:.3f}  pitch={msg.pitch:.3f}")
