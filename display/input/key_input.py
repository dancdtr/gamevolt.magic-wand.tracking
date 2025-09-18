import tkinter as tk
from collections.abc import Callable

from gamevolt.events.event import Event


class KeyInput:
    def __init__(self, root: tk.Misc) -> None:
        self.root = root

        self.root.bind_all("<Escape>", lambda e: self.escaped.invoke())

        self.escaped: Event[Callable[[], None]] = Event()
