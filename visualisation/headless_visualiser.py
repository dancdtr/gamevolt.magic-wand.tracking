from collections.abc import Callable

from gamevolt.events.event import Event
from visualisation.visualiser_protocol import WandVisualiserProtocol


class HeadlessVisualiser(WandVisualiserProtocol):
    def __init__(self) -> None:
        super().__init__()
        self._quit: Event[Callable[[], None]] = Event()

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit
