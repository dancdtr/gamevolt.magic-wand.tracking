import tkinter as tk
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.visualisation.canvas_factory import CanvasFactory
from gamevolt.visualisation.configuration.visualiser_settings import VisualiserSettings
from gamevolt.visualisation.key_handler import KeyHandler
from gamevolt.visualisation.root_factory import RootFactory
from gamevolt.visualisation.visualiser_protocol import VisualiserProtocol


class Visualiser(VisualiserProtocol):
    def __init__(self, settings: VisualiserSettings) -> None:
        self._root = RootFactory(settings.root).create()
        self._canvas = CanvasFactory(settings.canvas, self._root).create()

        self._key_handler = KeyHandler(self._root)

        self._is_running = False

        self._quit: Event[Callable[[], None]] = Event()

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    @property
    def root(self) -> tk.Tk:
        return self._root

    @property
    def canvas(self) -> tk.Canvas:
        return self._canvas

    def start(self) -> None:
        if self._is_running:
            return

        self._is_running = True

        self._key_handler.register_key_callback("q", self._on_quit)
        self._canvas.bind("<Configure>", lambda e: self._on_resize_window)

    def stop(self) -> None:
        if not self._is_running:
            return

        self._canvas.unbind_all("<Configure>")
        self._key_handler.unregister_key_callback("q", self._on_quit)

        self._root.destroy()

        self._is_running = False

    def update(self) -> None:
        if not self._is_running:
            return

        self._root.update_idletasks()
        self._root.update()

    def register_key_callback(self, key: str, callback: Callable[[], None]) -> None:
        self._root.bind(key, lambda e: callback())

    def unregister_key_callbacks(self, key: str) -> None:
        self._root.unbind(key)

    def _on_resize_window(self) -> None:
        pass

    def _on_quit(self) -> None:
        print("Quitting...")
        self.quit.invoke()
