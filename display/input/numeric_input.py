import tkinter as tk
from collections.abc import Callable

from display.input.key_input import KeyInput
from gamevolt.events.event import Event
from gamevolt.toolkit.timer import Timer

_INPUT_DURATION = 0.8
_MAX_LENGTH = 2


class NumericInput(KeyInput):
    def __init__(self, root: tk.Misc) -> None:
        # super().__init__(root)
        self.root = root

        self._timer = Timer(_INPUT_DURATION)
        self._input_str = ""

        for key in range(10):
            self.root.bind_all(f"<Key-{key}>", lambda e, x=str(key): self._on_alpha_key_pressed(x))

        self.updated: Event[Callable[[int], None]] = Event()

        self._timer.start()

    @property
    def input_str(self) -> str:
        return self._input_str

    def get_input_int(self) -> int | None:
        return int(self._input_str)

    def _on_alpha_key_pressed(self, key: str) -> None:
        if self._timer.is_complete or len(self._input_str) >= _MAX_LENGTH:
            self._input_str = key
            self._timer.restart()
        else:
            self._input_str += key

        self.updated.invoke(int(self._input_str))
