from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

from gamevolt.events.event import Event
from gamevolt.logging import Logger


class _LineSource(Protocol):
    @property
    def line_received(self) -> Event[Callable[[str], None]]: ...


class WandRebootDetector:
    """Detect wand reboots from the anchor stream.

    Subscribes to the same line source as the IMU stream and watches for
    `$PEKIO,PP,<seq>,0x<tag>,VERS,<value>` — the boot banner the wand
    emits on power-on (rail brown-out, battery reseat, OTA stall, ...).
    Fires `wand_rebooted(tag)` once per reboot; the banner ships 5x in a
    row at boot, so per-tag duplicates within `_DEDUP_WINDOW_S` are
    suppressed.

    Tags are normalised to bare uppercase hex (no `0x` prefix) to match
    the rest of the wand pipeline.
    """

    _DEDUP_WINDOW_S = 2.0
    _LINE_PREFIX = "$PEKIO,PP,"
    _BOOT_BANNER_FIELD = "VERS"

    def __init__(self, logger: Logger, line_source: _LineSource) -> None:
        self._logger = logger
        self._line_source = line_source
        self._wand_rebooted: Event[Callable[[str], None]] = Event()
        self._last_fire_monotonic: dict[str, float] = {}

    @property
    def wand_rebooted(self) -> Event[Callable[[str], None]]:
        return self._wand_rebooted

    def start(self) -> None:
        self._line_source.line_received.subscribe(self._on_line)

    def stop(self) -> None:
        self._line_source.line_received.unsubscribe(self._on_line)

    def _on_line(self, line: str) -> None:
        if not line.startswith(self._LINE_PREFIX):
            return

        fields = line.split(",")
        # $PEKIO,PP,<seq>,0x<tag>,VERS,<value>
        if len(fields) < 6 or fields[4] != self._BOOT_BANNER_FIELD:
            return

        tag = self._normalise_tag(fields[3])

        now = time.monotonic()
        last = self._last_fire_monotonic.get(tag)
        if last is not None and (now - last) < self._DEDUP_WINDOW_S:
            return
        self._last_fire_monotonic[tag] = now

        self._logger.info(f"Wand ({tag}) reboot detected (PP,VERS banner).")
        self._wand_rebooted.invoke(tag)

    @staticmethod
    def _normalise_tag(raw: str) -> str:
        s = raw.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        return s.upper()
