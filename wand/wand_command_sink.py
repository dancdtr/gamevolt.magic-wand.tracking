from __future__ import annotations

from typing import Protocol

from gamevolt.messaging.message import Message


class WandCommandSink(Protocol):
    """Routes commands to a wand. Implementation chooses the transport
    (anchor-relay WebSocket today; Eliko command channel later)."""

    def send_to_wand(self, wand_id: str, message: Message) -> None:
        """Route via the single anchor currently servicing the wand."""
        ...

    def broadcast_to_wand(self, wand_id: str, message: Message) -> None:
        """Send via every connected anchor so the wand receives the
        message regardless of which anchor it is tuned to."""
        ...
