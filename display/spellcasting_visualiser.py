# display/gesture_display.py
from __future__ import annotations

import asyncio
from collections.abc import Callable
from logging import Logger

from PIL import ImageTk
from PIL.ImageTk import PhotoImage as _PhotoImage

from classification.classifiers.spells.spell import Spell
from classification.gesture_type import GestureType
from detection.gesture_history import GestureHistory
from display.gesture_history_view import GestureHistoryView
from display.images.libraries.gesture_image_library import GestureImageLibrary
from display.images.libraries.spell_image_library import SpellImageLibrary
from gamevolt.display.image_visualiser import ImageVisualiser
from gamevolt.events.event import Event
from input.spell_provider import SpellProvider
from spell_type import SpellType


class SpellcastingVisualiser:
    def __init__(
        self,
        logger: Logger,
        spell_image_library: SpellImageLibrary,
        gesture_image_library: GestureImageLibrary,
        visualiser: ImageVisualiser,
        gesture_history: GestureHistory,
        spell_selector: SpellProvider,
    ):
        self._logger = logger

        self._gesture_image_library = gesture_image_library
        self._spell_image_library = spell_image_library
        self._gesture_history = gesture_history
        self._spell_provider = spell_selector
        self._visualiser = visualiser

        # history UI
        self._history_view = GestureHistoryView(
            visualiser=self._visualiser,
            parent=self._visualiser.history_bar,
            icon_provider=self._gesture_image_library,
            max_visible=15,
            icon_pad=0,
        )

        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False

        self.target_spell_updated: Event[Callable[[SpellType], None]] = Event()
        self.escaped: Event[Callable[[], None]] = Event()

    def start(self) -> None:
        if self._running:
            return
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError as exc:
            raise RuntimeError("GestureDisplay.start() must be called inside an asyncio event loop.") from exc

        # IMPORTANT: start the visualiser first so Tk root exists
        self._visualiser.start()

        # Load the library AFTER the root exists; if your library supports it,
        # pass the Tk master so PhotoImages bind to this window's interpreter.
        try:
            # preferred API (add this param in your library if you can)
            self._spell_image_library.load(tk_master=self._visualiser.root)  # type: ignore[arg-type]
            self._gesture_image_library.load(tk_master=self._visualiser.root)  # type: ignore[arg-type]
        except TypeError:
            # fallback to legacy load()
            self._spell_image_library.load()
            self._gesture_image_library.load()  # type: ignore[arg-type]

        self._history_view.bind_model(self._gesture_history)

        try:
            self._visualiser.root.deiconify()
        except Exception:
            pass

        self._visualiser.escaped.subscribe(self._on_escaped)
        self._spell_provider.target_spells_updated.subscribe(self._on_spells_updated)

        self._running = True

    def stop(self) -> None:
        if not self._running:
            try:
                self._visualiser.stop()
            finally:
                return

        self._spell_provider.target_spells_updated.unsubscribe(self._on_spells_updated)
        self.escaped.unsubscribe(self._on_escaped)
        self._visualiser.stop()
        self._running = False

    def show_spell(self, type: SpellType) -> None:
        img = self._spell_image_library.get_image(type)
        self._logger.debug(f"Show pic for: {type.name}")

        if img is None:
            self._visualiser.clear_image()
            return

        # If it's a PhotoImage from a different Tk interpreter, rebind via PIL:
        if isinstance(img, _PhotoImage) and getattr(img, "tk", None) is not self._visualiser.root.tk:
            try:
                pil = ImageTk.getimage(img).copy()
                self._visualiser.post_image(pil)  # visualiser will bind master=self.root
                return
            except Exception as e:
                self._logger.warning(f"Rebind failed: {e}")
                # fall through to best-effort post

        self._visualiser.post_image(img)

    def _on_escaped(self) -> None:
        self._logger.info("Escape key pressed...")
        self.escaped.invoke()

    def _on_spells_updated(self, spells: list[Spell]) -> None:
        # TODO temp display only 1 spell
        if spells:
            type = spells[0].type
            self._visualiser.post_image(self._spell_image_library.get_image(type))
