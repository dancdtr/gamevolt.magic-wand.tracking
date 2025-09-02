# arrow_display.py
import tkinter as tk
from collections.abc import Callable
from logging import Logger

from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType
from display.gesture_image_library import GestureImageLibrary, ImageLibrarySettings
from gamevolt.events.event import Event
from input.spell_selector import SpellSelector
from spell_type import SpellType


class ArrowDisplay:
    """
    Composition-style window. The first instance should pass master=None (creates tk.Tk()).
    Any additional windows should pass master=<root> (creates tk.Toplevel()).
    Always use .root to access the window object.
    """

    def __init__(self, logger: Logger, image_size: int, assets_dir: str, *, master: tk.Misc | None = None, title):
        self.size = image_size
        self.assets_dir = assets_dir

        self._logger = logger

        if master is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(master)

        self.root.title(title)

        self.root.geometry(f"{image_size}x{image_size}")
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

        self.label = tk.Label(self.root)
        self.label.pack(expand=True, fill="both")

        self._image_library = GestureImageLibrary(ImageLibrarySettings(assets_dir=assets_dir, image_size=image_size))
        self._spell_selector = SpellSelector(logger=logger, root=self.root)

        self._current_img: PhotoImage | None = None

        self.target_spell_updated: Event[Callable[[SpellType], None]] = Event()
        self.escaped: Event[Callable[[], None]] = Event()

    def start(self) -> None:
        self._image_library.load()
        self._spell_selector.start()

        self._spell_selector.target_updated.subscribe(self._on_spell_updated)

    def stop(self) -> None:
        self._spell_selector.target_updated.unsubscribe(self._on_spell_updated)

        self._spell_selector.stop()

        if self.root.winfo_exists():
            self.root.destroy()

    def update(self) -> None:
        # Optional convenience if you prefer display.update()
        self.root.update_idletasks()
        self.root.update()

    def show(self, gesture_type: GestureType) -> None:
        img = self._image_library.get_image(gesture_type)
        if img is not None:
            self._current_img = img
            self.label.config(image=img)

    def _on_spell_updated(self, type: SpellType) -> None:
        self._logger.info(f"Target updated: {type.name}")
        self.target_spell_updated.invoke(type)

    def _on_escape(self) -> None:
        self._logger.debug("Escape key pressed...")
        self.escaped.invoke()
