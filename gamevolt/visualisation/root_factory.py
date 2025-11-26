import tkinter as tk

from gamevolt.visualisation.configuration.preview_settings import RootSettings


class RootFactory:
    def __init__(self, settings: RootSettings) -> None:
        self._settings = settings

    def create(self) -> tk.Tk:
        root = tk.Tk()
        root.title(self._settings.title)
        root.geometry(self._settings.geometry)

        return root
