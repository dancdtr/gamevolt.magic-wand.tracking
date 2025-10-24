import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from tk_key_handler import TkKeyHandler


@dataclass
class TkPreviewSettings:
    title: str
    width: int
    height: int
    buffer: int

    @property
    def geometry(self) -> str:
        return f"{self.width}x{self.height}+{self.buffer}+{self.buffer}"


class TkPreview:
    def __init__(
        self,
        settings: TkPreviewSettings,
    ) -> None:
        self._root = tk.Tk()
        self._root.title(settings.title)

        self._key_handler = TkKeyHandler(self._root)

        self._root.geometry(settings.geometry)
        self._canvas = tk.Canvas(self._root, bg="#222", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._status = tk.Label(self._root, text="", fg="#ddd", bg="#111")
        self._status.pack(side="bottom", fill="x")

    def start(self) -> None:
        # self.register_key_callback("q", self._root.destroy)
        self._key_handler.register_key_callback("q", self._root.destroy)
        self._key_handler.unregister_key_callback("q", self._root.destroy)
        self._key_handler.register_key_callback("q", self._root.destroy)

    def stop(self) -> None:
        self._key_handler.register_key_callback("q", self._root.destroy)

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
