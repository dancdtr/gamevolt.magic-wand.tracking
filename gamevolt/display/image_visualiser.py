# gamevolt/display/image_visualiser.py
from __future__ import annotations

import asyncio
import queue
import sys
import threading
import tkinter as tk
from typing import Optional

from PIL import ImageTk
from PIL.Image import Image as PILImage
from PIL.ImageTk import PhotoImage

from gamevolt.display.configuration.image_visualiser_settings import ImageVisualiserSettings


class ImageVisualiser:
    """
    Generic Tk window that manages its own async GUI loop and shows images.
    Post images from any thread with .post_image(img). Pass None to clear.
    """

    def __init__(self, settings: ImageVisualiserSettings, master: tk.Misc | None = None):
        if sys.platform == "darwin" and threading.current_thread() is not threading.main_thread():
            raise RuntimeError("On macOS, Tk must be created on the main thread.")

        self._settings = settings

        # Root/Toplevel
        existing = getattr(tk, "_default_root", None)
        if master is None:
            if existing is not None:
                # Reuse the existing interpreter; create our window as a Toplevel
                self.root = tk.Toplevel(existing)
            else:
                self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(master)

        self.root.title(settings.title)
        self.root.geometry(f"{settings.width}x{settings.height}")
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

        # --- Toolbar at the top (for dropdowns, buttons, etc.) ---
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(side="top", fill="x")

        # --- Content area fills the rest ---
        self.content = tk.Frame(self.root)
        self.content.pack(side="top", fill="both", expand=True)

        # Image label goes inside content area
        self._label = tk.Label(self.content)
        self._label.pack(expand=True, fill="both")

        # Internal state
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None
        self._running = False

        # Thread-safe inbox for posted images (coalescing queue)
        self._inbox: queue.Queue[PhotoImage | PILImage | None] = queue.Queue(maxsize=1)

        self._current_img: Optional[PhotoImage] = None  # keep reference to avoid GC
        self._tk_thread_id: Optional[int] = threading.get_ident()  # for debugging

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Start the internal GUI loop task. Must be called inside an asyncio loop."""
        if self._task is not None:
            return
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError as exc:
            raise RuntimeError("ImageVisualiser.start() must be called inside an asyncio event loop.") from exc

        self._running = True
        self._task = self._loop.create_task(self._gui_loop(), name="ImageVisualiser.GUI")

    def stop(self) -> None:
        """Stop the GUI loop and destroy the window."""
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

    def post_image(self, image: PhotoImage | PILImage | None) -> None:
        """
        Thread/loop-safe: queue an image update. Pass None to clear.
        Accepts PhotoImage (preferred) or a PIL.Image (auto-converted in the GUI thread).
        """
        self._queue_image(image)

    def clear_image(self) -> None:
        self._queue_image(None)

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _queue_image(self, img: PhotoImage | PILImage | None) -> None:
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
        delay = 1 / self._settings.fps
        try:
            while self._running and self.root.winfo_exists():
                last: PhotoImage | PILImage | None = None
                try:
                    while True:
                        last = self._inbox.get_nowait()
                except queue.Empty:
                    pass

                # ✅ Only update when we actually got a new item
                if last is not None:
                    self._apply(last)

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

    def _apply(self, img: PhotoImage | PILImage | None) -> None:
        if img is None:
            self._current_img = None
            self._label.config(image="")
            return

        if isinstance(img, PILImage):
            # Bind to this Tk root to avoid master-mismatch issues
            img = ImageTk.PhotoImage(img, master=self.root)

        self._current_img = img
        self._label.config(image=img)
