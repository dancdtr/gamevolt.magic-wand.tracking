import tkinter as tk

from gamevolt.visualisation.configuration.axes_settings import AxesSettings


class Axes:
    def __init__(self, settings: AxesSettings, canvas: tk.Canvas) -> None:
        self._settings = settings
        self._canvas = canvas

        self._axes_ids: list[int] = []

    def draw(self) -> None:
        self.clear()
        if not self._settings.show_axes:
            return

        w = max(self._canvas.winfo_width(), 1)
        h = max(self._canvas.winfo_height(), 1)
        cx = w // 2
        cy = h // 2

        # Crosshair through the centre (matches centered coords)
        self._axes_ids.append(self._canvas.create_line(0, cy, w, cy, fill=self._settings.colour, width=self._settings.width))
        self._axes_ids.append(self._canvas.create_line(cx, 0, cx, h, fill=self._settings.colour, width=self._settings.width))

        self._axes_ids.append(self._canvas.create_rectangle(1, 1, w - 1, h - 1, outline=self._settings.colour, width=self._settings.width))

    def clear(self) -> None:
        for i in self._axes_ids:
            self._canvas.delete(i)
        self._axes_ids.clear()
