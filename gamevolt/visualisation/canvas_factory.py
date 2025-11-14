import tkinter as tk

from gamevolt.visualisation.configuration.canvas_settings import CanvasSettings


class CanvasFactory:
    def __init__(self, settings: CanvasSettings, root: tk.Tk) -> None:
        self._settings = settings
        self._root = root

    def create(self) -> tk.Canvas:
        canvas = tk.Canvas(
            self._root,
            bg=self._settings.background_colour,
            highlightthickness=self._settings.highlight_thickness,
        )
        canvas.pack(fill="both", expand=True)

        return canvas
