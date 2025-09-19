# display/gesture_history_view.py
from __future__ import annotations

import tkinter as tk

from PIL.Image import Image as PILImage
from PIL.ImageTk import PhotoImage

from detection.detected_gestures import DetectedGestures
from detection.gesture_history import GestureHistory
from display.image_libraries.gesture_image_library import GestureImageLibrary
from gamevolt.display.image_visualiser import ImageVisualiser


class GestureHistoryView:
    def __init__(
        self,
        visualiser: ImageVisualiser,
        *,
        parent: tk.Misc | None = None,
        icon_provider: GestureImageLibrary,
        history: GestureHistory,
        max_visible: int,
        icon_pad: int,
    ) -> None:
        self._vis = visualiser
        self._root = parent or self._vis.history_bar
        self._icon_provider = icon_provider
        self._max_visible = max_visible
        self._history = history
        self._pad = icon_pad

        # container frame (horizontal flow)
        self._frame = tk.Frame(self._root)
        self._frame.pack(side="left", fill="x", expand=True)

        # keep refs to currently displayed icons
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

        if self._enabled:
            pass
        else:
            self._schedule_render()

    # --- internal ---------------------------------------------------------

    def _on_history_updated(self) -> None:
        # This may be called from non-GUI threads → marshal to Tk thread.
        self._schedule_render()

    def _schedule_render(self) -> None:
        if self._dirty:
            return

        self._dirty = True
        self._vis.post_ui(self._render)

    def _render(self) -> None:
        self._dirty = False

        # Clear existing widgets
        for child in list(self._frame.children.values()):
            child.destroy()
        self._icon_refs.clear()

        records: list[DetectedGestures] = self._history.items() if self._history and self._enabled else []

        if not records:
            return

        # Show only the last N
        subset = records[-self._max_visible :]

        for record in subset:
            icon = self._icon_provider.get_image(record.main_gesture)  # TODO show all gestures, not just main
            if icon is None:
                continue

            if isinstance(icon, PILImage):
                icon = PhotoImage(icon, master=self._vis.root)

            lbl = tk.Label(self._frame, image=icon)
            lbl.pack(side="left", padx=self._pad, pady=4)
            self._icon_refs.append(icon)  # keep a ref
