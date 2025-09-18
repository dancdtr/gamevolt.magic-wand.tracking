# display/gesture_display.py
from __future__ import annotations

import asyncio
from collections.abc import Callable
from logging import Logger

from PIL.ImageTk import PhotoImage

from detection.gesture_history import GestureHistory
from display.gesture_history_view import GestureHistoryView
from display.image_libraries.gesture_image_library import GestureImageLibrary
from display.image_libraries.spell_image_library import SpellImageLibrary
from display.input.display_spell_provider import DisplaySpellProvider
from gamevolt.display.image_visualiser import ImageVisualiser
from gamevolt.events.event import Event
from spells.spell import Spell
from spells.spell_type import SpellType


class SpellcastingVisualiser:
    def __init__(
        self,
        logger: Logger,
        spell_image_library: SpellImageLibrary,
        gesture_image_library: GestureImageLibrary,
        visualiser: ImageVisualiser,
        gesture_history: GestureHistory,
        spell_selector: DisplaySpellProvider,
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
            max_visible=8,
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

        self._spell_image_library.load(tk_master=self._visualiser.root)
        self._gesture_image_library.load(tk_master=self._visualiser.root)

        self._history_view.bind_model(self._gesture_history)

        self._visualiser.root.deiconify()

        self._visualiser.escaped.subscribe(self._on_escaped)
        self._spell_provider.target_spells_updated.subscribe(self._on_spells_updated)

        self._running = True

    def stop(self) -> None:
        if self._running:
            self._visualiser.stop()

        self._spell_provider.target_spells_updated.unsubscribe(self._on_spells_updated)
        self.escaped.unsubscribe(self._on_escaped)
        self._visualiser.stop()
        self._running = False

    def show_spell_instruction(self, spell_type: SpellType) -> None:
        image = self._spell_image_library.get_spell_instruction_image(spell_type)  # TODO temp, allow multiple spell targets
        self._logger.debug(f"Show pic for: {spell_type.name}")

        self._show_image(image)

    def show_spell_cast(self, spell_type: SpellType) -> None:
        image = self._spell_image_library.get_spell_cast_image(spell_type)  # TODO temp,  handle multiple spell targets
        self._logger.debug(f"Show pic for: {spell_type.name}")

        self._show_image(image)

    def _show_image(self, image: PhotoImage | None) -> None:
        if image is None:
            self._visualiser.clear_image()
            return

        self._visualiser.post_image(image)

    def _on_escaped(self) -> None:
        self._logger.info("Escape key pressed...")
        self.escaped.invoke()

    def _on_spells_updated(self, spells: list[Spell]) -> None:
        # TODO temp display only 1 spell
        if spells:
            spell_type = spells[0].type
            self.show_spell_instruction(spell_type)
