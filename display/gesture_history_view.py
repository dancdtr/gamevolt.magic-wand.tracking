# display/gesture_history_view.py
from __future__ import annotations

import tkinter as tk

from PIL.Image import Image as PILImage
from PIL.ImageTk import PhotoImage

from detection.detected_gestures import DetectedGestures
from detection.gesture_history import GestureHistory
from display.image_libraries.gesture_image_library import GestureImageLibrary
from gamevolt.visualisation.visualiser import Visualiser


class GestureHistoryView:
    def __init__(
        self,
        visualiser: Visualiser,
        *,
        parent: tk.Misc | None = None,
        icon_provider: GestureImageLibrary,
        history: GestureHistory,
        max_visible: int,
        icon_pad: int,
    ) -> None:
        self._vis = visualiser
        self._root = parent or self._vis.root
        self._icon_provider = icon_provider
        self._max_visible = max_visible
        self._history = history
        self._pad = icon_pad

        self._frame = tk.Frame(self._root)
        self._frame.pack(side="left", fill="x", expand=True)

        self._icon_refs: list[PhotoImage] = []

        self._enabled = True
        self._dirty = False

    def start(self) -> None:
        self._history.updated.subscribe(self._on_history_updated)
        self._schedule_render()

    def stop(self) -> None:
        self._history.updated.unsubscribe(self._on_history_updated)
        self._schedule_render()

    def toggle(self) -> None:
        self._enabled = not self._enabled
        self._schedule_render()

    def _on_history_updated(self) -> None:
        self._schedule_render()

    def _schedule_render(self) -> None:
        if self._dirty:
            return

        self._dirty = True
        self._vis.post_ui(self._render)

    def _render(self) -> None:
        self._dirty = False

        for child in list(self._frame.children.values()):
            child.destroy()
        self._icon_refs.clear()

        records: list[DetectedGestures] = self._history.items() if self._history and self._enabled else []

        if not records:
            return

        subset = records[-self._max_visible :]

        for record in subset:
            icon = self._icon_provider.get_image(record.main_gesture)
            if icon is None:
                continue

            if isinstance(icon, PILImage):
                icon = PhotoImage(icon, master=self._vis.root)

            lbl = tk.Label(self._frame, image=icon)
            lbl.pack(side="left", padx=self._pad, pady=4)
            self._icon_refs.append(icon)
