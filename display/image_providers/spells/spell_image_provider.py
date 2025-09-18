import os
from typing import Iterable

from PIL import Image
from PIL.Image import Image as PILImage

from display.image_providers.configuration.image_provider_settings import ImageProviderSettings
from gamevolt.display.pil_image_provider import PILImageProvider, load_image, recolour_bg
from spells.spell_type import SpellType


class SpellImageProvider(PILImageProvider[SpellType]):
    def __init__(self, settings: ImageProviderSettings) -> None:
        super().__init__()
        self._settings = settings

        self._image_library: dict[SpellType, PILImage] = {}

    @property
    def image_library(self) -> dict[SpellType, PILImage]:
        return self._image_library

    def items(self) -> Iterable[tuple[SpellType, PILImage]]:
        return self._image_library.items()

    def get_image(self, type: SpellType) -> PILImage | None:
        return self.image_library.get(type)

    def load(self) -> None:
        # for type in SpellType: #TODO: implement all spells
        for type in SpellType:
            file = f"{type.name.lower()}.png"

            path = os.path.join(self._settings.assets_dir, file)

            base_image = load_image(path)
            size = (self._settings.image_size, self._settings.image_size)

            base_image = base_image.resize(size, Image.Resampling.LANCZOS)
            base_image = recolour_bg(base_image, self._settings.bg_colour)
            # base_image = recolour_icon(base_image, self._settings.icon_colour)

            self._image_library[type] = base_image
