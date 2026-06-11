"""Per-player consecutive-failure counter, feeding the pity (struggle) bonus.

Each failed/unrecognised attempt increments the streak; any successful cast resets it.
The scorer reads the streak to lift a struggling guest up to (but no higher than) the
lowest quality tier. Conceptually hub-side per-player state; in-memory stub for now.
"""

from __future__ import annotations

from typing import Protocol


class StreakTracker(Protocol):
    def failed_streak(self, player_id: str) -> int: ...

    def record_fail(self, player_id: str) -> None: ...

    def reset(self, player_id: str) -> None: ...


class InMemoryStreakTracker:
    def __init__(self) -> None:
        self._fails: dict[str, int] = {}

    def failed_streak(self, player_id: str) -> int:
        return self._fails.get(player_id, 0)

    def record_fail(self, player_id: str) -> None:
        self._fails[player_id] = self._fails.get(player_id, 0) + 1

    def reset(self, player_id: str) -> None:
        self._fails.pop(player_id, None)
