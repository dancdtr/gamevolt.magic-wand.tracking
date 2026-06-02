from __future__ import annotations

from typing import Protocol


class ElikoCommandClient(Protocol):
    """Outbound command channel for Eliko-format PEKIO commands.

    Implemented by both `ElikoClient` (TCP, RTLS Server) and
    `ElikoSingleAnchorClient` (serial, single anchor) so the same
    `ElikoWandCommandSink` can sit on either transport.
    """

    def send_command(self, command: str) -> None: ...
