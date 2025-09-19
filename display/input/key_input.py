import tkinter as tk
from collections.abc import Callable

from gamevolt.events.event import Event


class KeyInput:
    def __init__(self, root: tk.Misc) -> None:
        self.root = root

        self.root.bind_all("<Key-q>", lambda e: self.quit.invoke())
        self.root.bind_all("<Key-h>", lambda e: self.toggle_history.invoke())
        self.root.bind_all("<Up>", lambda e: self.cycle_spell.invoke(-1))
        self.root.bind_all("<Down>", lambda e: self.cycle_spell.invoke(1))

        self.quit: Event[Callable[[], None]] = Event()
        self.toggle_history: Event[Callable[[], None]] = Event()
        self.cycle_spell: Event[Callable[[int], None]] = Event()
