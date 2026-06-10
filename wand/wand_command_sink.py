from __future__ import annotations

from typing import Protocol


class WandCommandSink(Protocol):
    """LED feedback channel to a wand. Implementations own the transport
    (PEKIO over serial/TCP today) and any per-wand state needed to render
    cues (idle flag + pulse-restore timer for the Eliko sink).

    Three cues at present:

    - `enter_idle` — slow fade in the sink's configured idle colour.
      Used while the wand is active in a zone.
    - `exit_idle`  — hold LEDs off (fade-mode zero). Cancels any pending
      pulse restore.
    - `fade_pulse` — fade in `colour` at `step` for `duration_s`. When the
      pulse ends, the sink restores idle if the wand is still flagged
      idle, else holds off.

    Haptic is intentionally not on this surface — see
    `docs/spec.md` §4.5 for the firmware brown-out background.
    """

    def enter_idle(self, wand_id: str) -> None: ...

    def exit_idle(self, wand_id: str) -> None: ...

    def fade_pulse(
        self,
        wand_id: str,
        colour: str,
        step: int,
        duration_s: float,
    ) -> None: ...
