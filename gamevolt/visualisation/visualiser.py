# gamevolt/visualisation/visualiser.py
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from logging import Logger
from queue import SimpleQueue

from gamevolt.events.event import Event
from gamevolt.visualisation.canvas_factory import CanvasFactory
from gamevolt.visualisation.configuration.visualiser_settings import VisualiserSettings
from gamevolt.visualisation.key_handler import KeyHandler
from gamevolt.visualisation.root_factory import RootFactory


class Visualiser:
    def __init__(self, logger: Logger, settings: VisualiserSettings) -> None:
        self._logger = logger
        self._settings = settings

        self._root = RootFactory(settings.root).create()
        self._canvas = CanvasFactory(settings.canvas, self._root).create()
        self._key_handler = KeyHandler(self._root)

        self._is_running = False

        self._quit: Event[Callable[[], None]] = Event()
        self._ui_queue: SimpleQueue[Callable[[], None]] = SimpleQueue()

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
        self._canvas.bind("<Configure>", lambda e: self._on_resize_window())

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
        self._flush_ui_queue()

    def register_key_callback(self, key: str, callback: Callable[[], None]) -> None:
        self._root.bind(key, lambda e: callback())

    def unregister_key_callbacks(self, key: str) -> None:
        self._root.unbind(key)

    def post_ui(self, callback: Callable[[], None]) -> None:
        """Thread-safe: enqueue a callback to run on the Tk/UI thread."""
        self._ui_queue.put(callback)

    def _flush_ui_queue(self) -> None:
        while not self._ui_queue.empty():
            callback = self._ui_queue.get_nowait()
            try:
                callback()
            except Exception as ex:
                self._logger.error(ex)

    def _on_resize_window(self) -> None:
        pass

    def _on_quit(self) -> None:
        self.quit.invoke()
