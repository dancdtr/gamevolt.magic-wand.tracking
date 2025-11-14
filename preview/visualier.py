import tkinter as tk
from collections.abc import Callable

from preview.canvas_factory import CanvasFactory
from preview.configuration.visualiser_settings import VisualiserSettings
from preview.label_factory import LabelFactory
from preview.root_factory import RootFactory
from tk_key_handler import TkKeyHandler


class Visualiser:
    def __init__(self, settings: VisualiserSettings) -> None:
        self._root = RootFactory(settings.root).create()
        self._canvas = CanvasFactory(settings.canvas, self._root).create()
        self._status = LabelFactory(settings.label, self._root).create()

        self._key_handler = TkKeyHandler(self._root)

    def start(self) -> None:
        self._key_handler.register_key_callback("q", self._root.destroy)

    def stop(self) -> None:
        self._key_handler.unregister_key_callback("q", self._root.destroy)

    @property
    def root(self) -> tk.Tk:
        return self._root

    @property
    def canvas(self) -> tk.Canvas:
        return self._canvas

    def update(self) -> None:
        self._root.update_idletasks()
        self._root.update()

    def set_status(self, status: str) -> None:
        self._status.config(text=status)

    def register_key_callback(self, key: str, callback: Callable[[], None]) -> None:
        self._root.bind(key, lambda e: callback())

    def unregister_key_callbacks(self, key: str) -> None:
        self._root.unbind(key)
