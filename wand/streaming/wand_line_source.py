from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from gamevolt.events.event import Event


class WandLineSource(Protocol):
    """Inbound line channel for any text-line wand sensor source.

    Eliko's TCP RTLS client and USB-serial single-anchor client both
    satisfy this structurally; future line-emitting sources plug in here
    without the parsing layer seeing the transport.

    Distinct from `gamevolt.serial.LineReceiverProtocol` only because that
    one uses `start`/`stop` (sync transport convention); this seam uses
    `start_async`/`stop_async` to match `TcpClient` and the Eliko clients.
    """

    @property
    def line_received(self) -> Event[Callable[[str], None]]: ...

    async def start_async(self) -> None: ...

    async def stop_async(self) -> None: ...
