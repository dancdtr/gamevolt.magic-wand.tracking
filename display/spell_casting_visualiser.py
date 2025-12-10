# display/spellcasting_visualiser.py
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from logging import Logger

from PIL import ImageTk
from PIL.Image import Image as PILImage
from PIL.ImageTk import PhotoImage

from display.image_libraries.spell_image_library import SpellImageLibrary
from gamevolt.display.utils import recolour_region_by_threshold
from gamevolt.events.event import Event
from gamevolt.toolkit.utils import hex_to_rgb
from gamevolt.visualisation.visualiser import Visualiser
from spells.control.spell_controller import SpellController
from spells.spell import Spell
from spells.spell_type import SpellType
from visualisation.configuration.trail_settings import TrailColourSettings
from wand.configuration.input_settings import InputSettings


class SpellCastingVisualiser:
    def __init__(
        self,
        logger: Logger,
        settings: InputSettings,
        spell_image_library: SpellImageLibrary,
        visualiser: Visualiser,
        spell_controller: SpellController,
    ) -> None:
        self._logger = logger
        self._spell_image_library = spell_image_library
        self._visualiser = visualiser
        self._spell_controller = spell_controller

        self._is_running = False

        self.quit: Event[Callable[[], None]] = Event()

        root = self._visualiser.root

        try:
            self._visualiser.canvas.pack_forget()
        except Exception:
            pass

        self._toolbar = tk.Frame(root)
        self._toolbar.pack(side="top", fill="x")

        self._content = tk.Frame(root, bg="black")
        self._content.pack(side="top", fill="both", expand=True)
        self._content.pack_propagate(False)

        self._image_label = tk.Label(self._content, anchor="center", bg="black")
        self._image_label.pack(side="top", fill="both", expand=True)

        self._base_image: PILImage | None = None
        self._current_img: PhotoImage | None = None

        self._wand_colours: dict[str, TrailColourSettings] = {w.id.upper(): w.colour for w in settings.tracked_wands}

        self._content.bind("<Configure>", self._on_content_resized)

    @property
    def toolbar(self) -> tk.Frame:
        return self._toolbar

    def start(self) -> None:
        if self._is_running:
            return

        self._is_running = True

        self._visualiser.start()

        self._spell_image_library.load(tk_master=self._visualiser.root)

        self._spell_controller.target_spell_updated.subscribe(self._on_target_spell_updated)
        self._spell_controller.quit.subscribe(self._on_quit)

    def stop(self) -> None:
        if not self._is_running:
            return

        self._is_running = False

        self._spell_controller.target_spell_updated.unsubscribe(self._on_target_spell_updated)
        self._spell_controller.quit.unsubscribe(self._on_quit)

        self._visualiser.stop()

    def show_spell_instruction(self, spell: Spell) -> None:
        image = self._spell_image_library.get_spell_instruction_image(spell.type)
        self._logger.debug(f"Show instruction for spell: {spell.name}")
        self._set_base_image(image)

    def show_spell_cast(self, spell_type: SpellType) -> None:
        image = self._spell_image_library.get_spell_cast_image(spell_type)
        self._logger.debug(f"Show cast image for spell: {spell_type.name}")
        self._set_base_image(image)

    def show_spell_cast_coloured(self, spell_type: SpellType, wand_id: str) -> None:
        wand_id = wand_id.upper()
        colour_settings = self._wand_colours.get(wand_id)
        rgb = (255, 255, 255) if colour_settings is None else hex_to_rgb(colour_settings.line_color)

        # IMPORTANT: do not touch ImageTk / PhotoImage off the UI thread.
        def apply() -> None:
            image = self._spell_image_library.get_spell_instruction_image(spell_type)
            if image is None:
                self._base_image = None
                self._rescale_image()
                return

            # Convert to PIL.Image on the UI thread (PhotoImage -> PIL)
            if isinstance(image, PhotoImage):
                pil_img = ImageTk.getimage(image)
            else:
                pil_img = image

            recoloured = recolour_region_by_threshold(
                pil_img,
                color=rgb,
                thresh=250,
                select_above=True,  # recolour dark pixels (glyph)
            )

            self._base_image = recoloured.copy()
            self._rescale_image()

        self._visualiser.post_ui(apply)

    def _set_base_image(self, image: PILImage | PhotoImage | None) -> None:
        def apply() -> None:
            if image is None:
                self._base_image = None
                self._rescale_image()
                return

            # Accept either PIL.Image or PhotoImage
            if isinstance(image, PhotoImage):
                from PIL import ImageTk

                pil_img = ImageTk.getimage(image)
            else:
                pil_img = image

            self._base_image = pil_img.copy()
            self._rescale_image()

        self._visualiser.post_ui(apply)

    def _rescale_image(self) -> None:
        if self._base_image is None:
            self._current_img = None
            self._image_label.config(image="", bg="black")
            return

        width = self._content.winfo_width()
        height = self._content.winfo_height()

        if width <= 1 or height <= 1:
            return

        img = self._base_image.copy()
        img.thumbnail((width, height))

        photo = PhotoImage(img)
        self._current_img = photo
        self._image_label.config(image=photo, bg="black")

    def _on_content_resized(self, event: tk.Event) -> None:
        self._rescale_image()

    def _on_target_spell_updated(self, spell: Spell | None) -> None:
        if spell is None:
            self._logger.debug("Target spell updated with None")
            self._set_base_image(None)
            return

        self._logger.debug(f"Target spell updated; showing instruction for {spell.long_name}")
        self.show_spell_instruction(spell)

    def _on_quit(self) -> None:
        self._logger.info("Quit requested from spell controller")
        self.quit.invoke()
