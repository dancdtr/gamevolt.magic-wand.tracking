from typing import Callable

from gamevolt.events.event import Event
from wand.wand_client import WandClient
from wand.wand_rotation_raw import WandRotationRaw


class WandServerProtocol:
    @property
    def wand_rotation_raw_updated(self) -> Event[Callable[[WandRotationRaw], None]]: ...

    @property
    def wand_disconnected(self) -> Event[Callable[[WandClient], None]]: ...

    @property
    def wand_connected(self) -> Event[Callable[[WandClient], None]]: ...

    async def start_async(self) -> None: ...

    async def stop_async(self) -> None: ...

    def update(self) -> None: ...
