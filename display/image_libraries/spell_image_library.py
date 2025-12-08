from enum import Enum, auto
from tkinter import Tk, Toplevel

from PIL.ImageTk import PhotoImage

from display.image_libraries.configuration.spell_image_library_settings import SpellImageLibrarySettings
from display.image_providers.spells.spell_image_provider import SpellImageProvider
from spells.spell import Spell
from spells.spell_type import SpellType


class SpellImageType(Enum):
    INSTRUCTION = auto()
    SUCCESS = auto()


class SpellImageLibrary:
    def __init__(self, settings: SpellImageLibrarySettings) -> None:
        self._settings = settings

        self._spell_instruction_active_provider = SpellImageProvider(settings.instruction)
        self._spell_success_provider = SpellImageProvider(settings.success)

        self._instruction_active_images: dict[SpellType, PhotoImage] = {}
        self._success_images: dict[SpellType, PhotoImage] = {}

    def load(self, tk_master: Toplevel | Tk) -> None:
        self._spell_instruction_active_provider.load()
        self._spell_success_provider.load()

        for spell_type, image in self._spell_instruction_active_provider.items():
            self._instruction_active_images[spell_type] = PhotoImage(image, master=tk_master)

        for spell_type, image in self._spell_success_provider.items():
            self._success_images[spell_type] = PhotoImage(image, master=tk_master)

    def get_spell_instruction_image(self, spell: Spell) -> PhotoImage:
        image_dict = self._instruction_active_images
        image = image_dict.get(spell.type)
        if image is not None:
            return image

        raise RuntimeError(f"No image to display for spell instruction: '{spell.type}'!")

    def get_spell_cast_image(self, spell_type: SpellType) -> PhotoImage:
        image = self._success_images.get(spell_type)
        if image is not None:
            return image

        raise RuntimeError(f"No image to display for spellcast: '{spell_type}'!")
