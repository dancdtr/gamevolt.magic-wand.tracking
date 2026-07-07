from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from typing import Protocol

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from wand.streaming.eliko.configuration.wand_battery_monitor_settings import WandBatteryMonitorSettings


class _BatteryClient(Protocol):
    @property
    def line_received(self) -> Event[Callable[[str], None]]: ...

    def poll_battery(self, tag: str, timeout_ms: int) -> None: ...


class WandBatteryMonitor:
    """Poll and report wand battery voltage over the anchor's OTA channel.

    Sends a GDHR poll per tracked tag every `poll_interval_s` and watches the
    line stream for the two shapes the voltage comes back in:

        $PEKIO,AC,123,0x<tag>,GDHR,voltages,0x<hex>,OTA   (poll response)
        $PEKIO,PP,<seq>,0x<tag>,GDHR,0x<hex>              (unsolicited report set)

    The hex value is millivolts. Fires `battery_updated(tag, millivolts,
    percent)`; percent is a rough linear map between the configured
    empty/full bounds — good enough to spot a dying cell, not a fuel gauge.
    """

    def __init__(
        self,
        logger: Logger,
        client: _BatteryClient,
        tracked_wand_ids: Iterable[str],
        settings: WandBatteryMonitorSettings,
    ) -> None:
        self._logger = logger
        self._client = client
        self._tracked_wand_ids = [self._normalise_tag(t) for t in tracked_wand_ids]
        self._settings = settings
        self._battery_updated: Event[Callable[[str, int, float], None]] = Event()
        self._poll_task: asyncio.Task[None] | None = None

    @property
    def battery_updated(self) -> Event[Callable[[str, int, float], None]]:
        return self._battery_updated

    def start(self) -> None:
        self._client.line_received.subscribe(self._on_line)
        self._poll_task = asyncio.create_task(self._poll_loop())

    def stop(self) -> None:
        if self._poll_task is not None:
            self._poll_task.cancel()
            self._poll_task = None
        self._client.line_received.unsubscribe(self._on_line)

    def poll_wand(self, tag: str) -> None:
        """Immediate one-off poll. Wired to wand-connect by the builder so a
        fresh reading lands on (re)connect instead of waiting out the
        interval tick.
        """
        normalised = self._normalise_tag(tag)
        if normalised not in self._tracked_wand_ids:
            return
        self._client.poll_battery(normalised, self._settings.timeout_ms)

    async def _poll_loop(self) -> None:
        while True:
            for tag in self._tracked_wand_ids:
                self._client.poll_battery(tag, self._settings.timeout_ms)
            await asyncio.sleep(self._settings.poll_interval_s)

    def _on_line(self, line: str) -> None:
        parsed = self._parse_gdhr(line)
        if parsed is None:
            return
        tag, millivolts = parsed

        if tag not in self._tracked_wand_ids:
            return

        percent = self._to_percent(millivolts)
        self._logger.info(f"Wand ({tag}) battery: {millivolts}mV (~{percent:.0f}%).")
        self._battery_updated.invoke(tag, millivolts, percent)

    @classmethod
    def _parse_gdhr(cls, line: str) -> tuple[str, int] | None:
        fields = line.split(",")
        try:
            if fields[0] == "$PEKIO" and fields[1] == "AC" and fields[4] == "GDHR" and fields[5] == "voltages":
                return cls._normalise_tag(fields[3]), int(fields[6], 16)
            if fields[0] == "$PEKIO" and fields[1] == "PP" and fields[4] == "GDHR":
                return cls._normalise_tag(fields[3]), int(fields[5], 16)
        except (IndexError, ValueError):
            return None
        return None

    def _to_percent(self, millivolts: int) -> float:
        span = self._settings.full_millivolts - self._settings.empty_millivolts
        if span <= 0:
            return 0.0
        fraction = (millivolts - self._settings.empty_millivolts) / span
        return max(0.0, min(1.0, fraction)) * 100.0

    @staticmethod
    def _normalise_tag(raw: str) -> str:
        s = raw.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        return s.upper()
