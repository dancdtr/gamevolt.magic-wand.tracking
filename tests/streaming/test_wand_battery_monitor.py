from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.logging._levels import register_custom_levels
from gamevolt.logging._logger import Logger
from wand.streaming.eliko.configuration.wand_battery_monitor_settings import WandBatteryMonitorSettings
from wand.streaming.eliko.wand_battery_monitor import WandBatteryMonitor

TAG = "1DAD"


def _logger() -> Logger:
    register_custom_levels()
    logging.setLoggerClass(Logger)
    log = logging.getLogger("test.wand_battery_monitor")
    log.setLevel(logging.WARNING)
    return log  # type: ignore[return-value]


class _FakeClient:
    def __init__(self) -> None:
        self._line_received: Event[Callable[[str], None]] = Event()
        self.polls: list[tuple[str, int]] = []

    @property
    def line_received(self) -> Event[Callable[[str], None]]:
        return self._line_received

    def poll_battery(self, tag: str, timeout_ms: int) -> None:
        self.polls.append((tag, timeout_ms))


def _monitor(client: _FakeClient, **settings_overrides) -> tuple[WandBatteryMonitor, list[tuple[str, int, float]]]:
    settings = WandBatteryMonitorSettings(enabled=True, **settings_overrides)
    monitor = WandBatteryMonitor(
        logger=_logger(),
        client=client,
        tracked_wand_ids=[TAG],
        settings=settings,
    )
    updates: list[tuple[str, int, float]] = []
    monitor.battery_updated.subscribe(lambda tag, mv, pct: updates.append((tag, mv, pct)))
    return monitor, updates


def test_parses_ota_poll_response() -> None:
    client = _FakeClient()
    monitor, updates = _monitor(client)
    monitor._on_line("$PEKIO,AC,123,0x1DAD,GDHR,voltages,0x00000529,OTA")

    assert updates == [(TAG, 1321, updates[0][2])]
    assert 0.0 <= updates[0][2] <= 100.0


def test_parses_unsolicited_pp_report() -> None:
    client = _FakeClient()
    monitor, updates = _monitor(client)
    monitor._on_line("$PEKIO,PP,017,0x1DAD,GDHR,0x000005F2")

    assert updates == [(TAG, 1522, updates[0][2])]


def test_ignores_non_gdhr_and_untracked_lines() -> None:
    client = _FakeClient()
    monitor, updates = _monitor(client)

    monitor._on_line("$PEKIO,AC,123,0x1DAD,CMD0,value,0x19000903,OTA")  # OTA delivery notice, not voltage
    monitor._on_line("$PEKIO,AC,041,0,STORED,num_free_OTA_slots=159")
    monitor._on_line("$PEKIO,PP,000,0x1DAD,VERS,0x05000000")  # boot banner
    monitor._on_line("$PEKIO,AC,123,0x1DAE,GDHR,voltages,0x00000529,OTA")  # untracked tag
    monitor._on_line("$PEKIO,PR,001,0x1D99,0x1DAD,003,0x00000073,0x32973852B4B5")
    monitor._on_line("garbage")
    monitor._on_line("$PEKIO,AC,123,0x1DAD,GDHR,voltages,not_hex,OTA")

    assert updates == []


def test_percent_mapping_clamps() -> None:
    client = _FakeClient()
    monitor, _ = _monitor(client, full_millivolts=1500, empty_millivolts=1100)

    assert monitor._to_percent(1500) == 100.0
    assert monitor._to_percent(1100) == 0.0
    assert monitor._to_percent(1300) == 50.0
    assert monitor._to_percent(1650) == 100.0  # clamped high
    assert monitor._to_percent(900) == 0.0  # clamped low


def test_poll_wand_polls_tracked_tag_only() -> None:
    client = _FakeClient()
    monitor, _ = _monitor(client, timeout_ms=1234)

    monitor.poll_wand("0x1dad")  # normalised to tracked tag
    monitor.poll_wand("1DAE")  # untracked — ignored

    assert client.polls == [(TAG, 1234)]


def test_poll_loop_sends_gdhr_per_tracked_tag() -> None:
    async def drive() -> _FakeClient:
        client = _FakeClient()
        monitor, _ = _monitor(client, poll_interval_s=0.01, timeout_ms=1234)
        monitor.start()
        await asyncio.sleep(0.035)
        monitor.stop()
        return client

    client = asyncio.run(drive())
    assert len(client.polls) >= 2
    assert client.polls[0] == (TAG, 1234)
