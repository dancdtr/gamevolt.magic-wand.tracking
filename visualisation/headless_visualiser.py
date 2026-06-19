from collections.abc import Callable

from gamevolt.events.event import Event
from visualisation.visualiser_protocol import WandVisualiserProtocol


class HeadlessVisualiser(WandVisualiserProtocol):
    def __init__(self) -> None:
        super().__init__()
        self._quit: Event[Callable[[], None]] = Event()
        self._reset_xp_requested: Event[Callable[[], None]] = Event()
        self._record_session_changed: Event[Callable[[bool, str], None]] = Event()

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    @property
    def reset_xp_requested(self) -> Event[Callable[[], None]]:
        return self._reset_xp_requested

    @property
    def record_session_changed(self) -> Event[Callable[[bool, str], None]]:
        return self._record_session_changed
