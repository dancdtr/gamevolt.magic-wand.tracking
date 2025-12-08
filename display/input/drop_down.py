import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable

from gamevolt.events.event import Event


class DropDown:
    def __init__(self, root: tk.Misc, items: dict[int, str]):
        self._root = root
        self._root.focus_set()

        drop_down_names = [f"{key} : {items[key]}" for key in items.keys()]

        self._ids_to_strings = {k: v for k, v in zip(items.keys(), drop_down_names)}
        self._strings_to_ids = {v: k for k, v in zip(items.keys(), drop_down_names)}

        top = tk.Frame(self._root)
        top.pack(fill="x", padx=150, pady=6)

        self._choice = tk.StringVar()
        self._combo = ttk.Combobox(top, textvariable=self._choice, values=drop_down_names, state="readonly")
        self._combo.pack(side="left")
        self._combo.current(0)

        self._combo.bind("<<ComboboxSelected>>", self._on_dropdown_updated)

        self.updated: Event[Callable[[int], None]] = Event()

    def show_value(self, id: int) -> None:
        self._combo.set(self._ids_to_strings[id])

    def _on_dropdown_updated(self, _) -> None:
        combo_name = self._choice.get()
        id = self._strings_to_ids.get(combo_name)

        if combo_name:
            self.updated.invoke(id)
