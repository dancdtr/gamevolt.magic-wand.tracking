import tkinter as tk

from gamevolt.visualisation.configuration.label_settings import LabelSettings


class LabelFactory:
    def __init__(self, settings: LabelSettings, root: tk.Tk) -> None:
        self._settings = settings
        self._root = root

    def create(self) -> tk.Label:
        label = tk.Label(
            self._root,
            text=self._settings.text,
            fg=self._settings.foreground_colour,
            background=self._settings.background_colour,
        )
        label.pack(side=self._settings.side.name.lower(), fill=self._settings.fill.name.lower())

        return label
