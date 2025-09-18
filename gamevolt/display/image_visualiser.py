# gamevolt/display/image_visualiser.py
from __future__ import annotations

import asyncio
import queue
import sys
import threading
import tkinter as tk
from collections.abc import Callable

from PIL.ImageTk import PhotoImage

from gamevolt.display.configuration.image_visualiser_settings import ImageVisualiserSettings
from gamevolt.events.event import Event


class ImageVisualiser:
    """
    Generic Tk window that manages its own async GUI loop and shows images.
    Post images from any thread with .post_image(img). Pass None to clear.
    """

    def __init__(self, settings: ImageVisualiserSettings, master: tk.Misc | None = None):
        if sys.platform == "darwin" and threading.current_thread() is not threading.main_thread():
            raise RuntimeError("On macOS, Tk must be created on the main thread.")

        self._settings = settings

        # Root/Toplevel — reuse default interpreter if it already exists
        existing = getattr(tk, "_default_root", None)
        if master is None:
            self.root = tk.Toplevel(existing) if existing is not None else tk.Tk()
        else:
            self.root = tk.Toplevel(master)

        self.root.title(settings.title)
        self.root.geometry(f"{settings.width}x{settings.height}")
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

        # --- Layout: toolbar (top), history (bottom), content (middle) ---
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(side="top", fill="x")

        self.history_bar = tk.Frame(self.root, height=80)
        self.history_bar.pack(side="bottom", fill="x")
        self.history_bar.pack_propagate(False)  # keep 80px even when empty

        self.content = tk.Frame(self.root)
        self.content.pack(side="top", fill="both", expand=True)
        self.content.pack_propagate(False)  # child widgets can't force resize

        # Big image label in content
        self._label = tk.Label(self.content, anchor="center")
        self._label.pack(side="top", fill="both", expand=True)

        # Internal state
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None
        self._running = False

        # Thread-safe inboxes
        self._inbox: queue.Queue[PhotoImage | None] = queue.Queue(maxsize=1)
        self._ui_jobs: queue.Queue[Callable[[], None]] = queue.Queue()

        self._current_img: PhotoImage | None = None

        self.root.bind("<Escape>", lambda _e: self._on_escaped())

        self.escaped: Event[Callable[[], None]] = Event()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        if self._task is not None:
            return
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError as exc:
            raise RuntimeError("ImageVisualiser.start() must be called inside an asyncio event loop.") from exc

        self._running = True
        self._task = self._loop.create_task(self._gui_loop(), name="ImageVisualiser.GUI")

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def post_image(self, image: PhotoImage | None) -> None:
        """Thread/loop-safe: queue an image update. Pass None to clear."""
        self._queue_image(image)

    def clear_image(self) -> None:
        self._queue_image(None)

    def post_ui(self, fn: Callable[[], None]) -> None:
        """Thread-safe: schedule a callable to run on the Tk/GUI thread."""
        try:
            self._ui_jobs.put_nowait(fn)
        except queue.Full:
            pass

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #
    def _queue_image(self, img: PhotoImage | None) -> None:
        # Coalesce: if full, drop the older item
        try:
            self._inbox.put_nowait(img)
        except queue.Full:
            try:
                _ = self._inbox.get_nowait()
            except queue.Empty:
                pass
            try:
                self._inbox.put_nowait(img)
            except queue.Full:
                pass

    async def _gui_loop(self) -> None:
        delay = 1 / max(1, int(self._settings.fps))
        try:
            while self._running and self.root.winfo_exists():
                # 1) run any queued UI jobs on the Tk thread
                try:
                    while True:
                        job = self._ui_jobs.get_nowait()
                        job()
                except queue.Empty:
                    pass

                # 2) drain image inbox (keep only the last)
                last: PhotoImage | None = None
                try:
                    while True:
                        last = self._inbox.get_nowait()
                except queue.Empty:
                    pass
                if last is not None:
                    self._apply(last)

                # 3) pump Tk
                try:
                    self.root.update_idletasks()
                    self.root.update()
                except tk.TclError:
                    break

                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            pass
        finally:
            try:
                if self.root.winfo_exists():
                    self.root.destroy()
            except tk.TclError:
                pass

    def _apply(self, img: PhotoImage | None) -> None:
        if img is None:
            self._current_img = None
            self._label.config(image="")
            return

        self._current_img = img
        self._label.config(image=img)

    def _on_escaped(self) -> None:
        self.escaped.invoke()
