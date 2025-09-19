import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable

from gamevolt.events.event import Event


class DropDown:
    def __init__(self, root: tk.Misc, values: list[str]):
        self._root = root
        self._root.focus_set()

        top = tk.Frame(self._root)
        top.pack(fill="x", padx=150, pady=6)

        self._choice = tk.StringVar()
        self._combo = ttk.Combobox(top, textvariable=self._choice, values=values, state="readonly")
        self._combo.pack(side="left")
        self._combo.current(0)

        self._combo.bind("<<ComboboxSelected>>", self._on_dropdown_updated)

        self.updated: Event[Callable[[str], None]] = Event()

    def show_value(self, value: str) -> None:
        self._combo.set(value)

    def _on_dropdown_updated(self, _) -> None:
        combo_name = self._choice.get()

        if combo_name:
            self.updated.invoke(combo_name)
