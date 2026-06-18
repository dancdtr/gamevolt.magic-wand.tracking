from __future__ import annotations

from logging import Logger


class NullWandCommandSink:
    """No-op `WandCommandSink` for deployments where the app does not drive the
    wand at all (LED / idle / pulse). On the RTLS path the RTLS system owns wand
    IMU + command state, so the app stays read-only on the wand and issues no
    commands. Satisfies the `WandCommandSink` protocol structurally.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def enter_idle(self, wand_id: str) -> None:
        self._logger.trace(f"NullWandCommandSink: enter_idle({wand_id}) ignored.")

    def exit_idle(self, wand_id: str) -> None:
        self._logger.trace(f"NullWandCommandSink: exit_idle({wand_id}) ignored.")

    def fade_pulse(self, wand_id: str, colour: str, step: int, duration_s: float) -> None:
        self._logger.trace(f"NullWandCommandSink: fade_pulse({wand_id}) ignored.")
