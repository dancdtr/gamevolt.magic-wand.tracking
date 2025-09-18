from enum import Enum, auto
from tkinter import Tk, Toplevel

from PIL.ImageTk import PhotoImage

from display.image_libraries.configuration.spell_image_library_settings import SpellImageLibrarySettings
from display.image_providers.spells.spell_image_provider import SpellImageProvider
from spells.spell_type import SpellType


class SpellImageType(Enum):
    INSTRUCTION = auto()
    SUCCESS = auto()
    FAILURE = auto()


class SpellImageLibrary:
    def __init__(self, settings: SpellImageLibrarySettings) -> None:
        self._settings = settings

        self._spell_instruction_provider = SpellImageProvider(settings.instruction)
        self._spell_success_provider = SpellImageProvider(settings.success)
        # self._spell_failure_provider = SpellImageProvider(settings.success)

    def load(self, tk_master: Toplevel | Tk) -> None:
        self._spell_instruction_provider.load()
        self._spell_success_provider.load()
        # self._spell_failure_provider.load()

        self._instruction_images: dict[SpellType, PhotoImage] = {}
        self._success_images: dict[SpellType, PhotoImage] = {}

        for type, image in self._spell_instruction_provider.items():
            self._instruction_images[type] = PhotoImage(image, master=tk_master)

        for type, image in self._spell_success_provider.items():
            self._success_images[type] = PhotoImage(image, master=tk_master)

    def get_spell_instruction_image(self, type: SpellType) -> PhotoImage:
        image = self._instruction_images.get(type)
        if image is not None:
            return image

        raise RuntimeError(f"No image to display for spell instruction: '{type}'!")

    def get_spell_cast_image(self, type: SpellType) -> PhotoImage:
        image = self._success_images.get(type)
        if image is not None:
            return image

        raise RuntimeError(f"No image to display for spellcast: '{type}'!")
