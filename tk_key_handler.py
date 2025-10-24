import tkinter as tk
from collections.abc import Callable


class TkKeyHandler:
    def __init__(self, root: tk.Tk) -> None:
        self._root = root

        self._key_registrations: dict[str, dict[type, str]] = {}

    def register_key_callback(self, key: str, callback: Callable[[], None]) -> None:
        func_id = self._root.bind(key, lambda e: callback())

        if not key in self._key_registrations:
            self._key_registrations[key] = {}

        key_dict = self._key_registrations[key]

        callback_type = type(callback)
        key_dict[callback_type] = func_id

    def unregister_key_callback(self, key: str, callback: Callable[[], None]) -> None:
        key_dict = self._key_registrations[key]
        if key_dict is None:
            return

        callback_type = type(callback)

        func_id = key_dict[callback_type]
        if func_id is None:
            return

        del key_dict[callback_type]

        if len(key_dict) == 0:
            del self._key_registrations[key]

        self._root.unbind(key, func_id)

    def unregister_key_callbacks(self, key: str) -> None:
        self._root.unbind(key)
