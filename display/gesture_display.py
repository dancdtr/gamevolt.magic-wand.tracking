# display/gesture_display.py
from __future__ import annotations

import asyncio
from collections.abc import Callable
from logging import Logger

from PIL import ImageTk
from PIL.Image import Image as PILImage
from PIL.ImageTk import PhotoImage
from PIL.ImageTk import PhotoImage as _PhotoImage

from classification.gesture_type import GestureType
from detection.gesture_history import GestureHistory
from display.gesture_history_view import GestureHistoryView
from display.gesture_image_library import GestureImageLibrary
from gamevolt.display.image_visualiser import ImageVisualiser
from gamevolt.events.event import Event
from input.spell_selector import SpellSelector
from spell_type import SpellType


class GestureDisplay:
    """
    Wrapper around ImageVisualiser:
      - Preloads GestureImageLibrary
      - Forwards .post(GestureType) to visualiser
      - Hosts SpellSelector and re-emits 'target_spell_updated'
    """

    def __init__(
        self,
        logger: Logger,
        big_image_library: GestureImageLibrary,
        small_image_library: GestureImageLibrary,
        visualiser: ImageVisualiser,
        gesture_history: GestureHistory,
    ):
        self._logger = logger
        self.visualiser = visualiser
        self._big_lib = big_image_library
        self._small_lib = small_image_library
        self._gesture_history = gesture_history

        self._spell_selector = SpellSelector(logger=logger, root=self.visualiser.toolbar)

        # history UI
        self._history_view = GestureHistoryView(
            visualiser=self.visualiser,
            parent=self.visualiser.history_bar,
            icon_provider=self._small_lib,
            max_visible=8,
            icon_pad=2,
        )

        self.target_spell_updated: Event[Callable[[SpellType], None]] = Event()
        self.escaped: Event[Callable[[], None]] = Event()

        self.visualiser.root.bind("<Escape>", lambda _e: self._on_escape())

        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError as exc:
            raise RuntimeError("GestureDisplay.start() must be called inside an asyncio event loop.") from exc

        # IMPORTANT: start the visualiser first so Tk root exists
        self.visualiser.start()

        # Load the library AFTER the root exists; if your library supports it,
        # pass the Tk master so PhotoImages bind to this window's interpreter.
        try:
            # preferred API (add this param in your library if you can)
            self._big_lib.load(tk_master=self.visualiser.root)  # type: ignore[arg-type]
            self._small_lib.load(tk_master=self.visualiser.root)  # type: ignore[arg-type]
        except TypeError:
            # fallback to legacy load()
            self._big_lib.load()
            self._small_lib.load()  # type: ignore[arg-type]

        self._spell_selector.start()
        self._spell_selector.target_updated.subscribe(self._on_spell_updated)
        self._history_view.bind_model(self._gesture_history)

        # Make sure the window is actually shown (in case it was withdrawn)
        try:
            self.visualiser.root.deiconify()
        except Exception:
            pass

        self._running = True

    def stop(self) -> None:
        if not self._running:
            try:
                self.visualiser.stop()
            finally:
                return

        try:
            self._spell_selector.target_updated.unsubscribe(self._on_spell_updated)
        except Exception:
            pass
        try:
            self._spell_selector.stop()
        except Exception:
            pass

        self.visualiser.stop()
        self._running = False

    def post(self, gesture: GestureType) -> None:
        img = self._big_lib.get_image(gesture)
        self._logger.debug(f"Show pic for: {gesture.name}")

        if img is None:
            self.visualiser.clear_image()
            return

        # If it's a PhotoImage from a different Tk interpreter, rebind via PIL:
        if isinstance(img, _PhotoImage) and getattr(img, "tk", None) is not self.visualiser.root.tk:
            try:
                pil = ImageTk.getimage(img).copy()
                self.visualiser.post_image(pil)  # visualiser will bind master=self.root
                return
            except Exception as e:
                self._logger.warning(f"Rebind failed: {e}")
                # fall through to best-effort post

        # Only post once here
        self.visualiser.post_image(img)

    def _on_spell_updated(self, t: SpellType) -> None:
        self._logger.info(f"Target updated: {t.name}")
        self.target_spell_updated.invoke(t)

    def _on_escape(self) -> None:
        self._logger.debug("Escape key pressed...")
        self.escaped.invoke()
