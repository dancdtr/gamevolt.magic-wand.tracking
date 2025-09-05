from PIL.ImageTk import PhotoImage

from display.image_providers.spells.spell_image_provider import SpellImageProvider
from display.images.libraries.configuration.image_library_settings import ImageLibrarySettings
from spell_type import SpellType


class SpellImageLibrary:
    def __init__(self, settings: ImageLibrarySettings) -> None:
        self._settings = settings

    def load(self) -> None:
        self._image_provider = SpellImageProvider(assets_dir=self._settings.assets_dir, image_size=self._settings.image_size)

    def get_image(self, type: SpellType) -> PhotoImage:
        image = self._image_provider.get_image(type)
        if image is not None:
            return image

        raise RuntimeError(f"No image to display for gesture: '{type}'!")
