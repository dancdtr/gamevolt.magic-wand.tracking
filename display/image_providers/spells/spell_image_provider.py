import os

from PIL.ImageTk import PhotoImage

from display.image_providers.image_provider import ImageProvider
from spell_type import SpellType


class SpellImageProvider(ImageProvider):
    def __init__(self, assets_dir: str, image_size: int) -> None:
        super().__init__(assets_dir)

        self._image_size = image_size

        self._image_library: dict[SpellType, PhotoImage] = self._generate()

    @property
    def image_library(self) -> dict[SpellType, PhotoImage]:
        return self._image_library

    def get_image(self, type: SpellType) -> PhotoImage | None:
        return self.image_library.get(type)

    def _generate(self) -> dict[SpellType, PhotoImage]:
        dict = {}
        # for type in SpellType: #TODO: implement all spells
        for type in [SpellType.NONE, SpellType.REVELIO]:
            png = f"{type.name.lower()}.png"
            path = os.path.join(self.assets_dir, png)
            image = self.load(path)

            dict[type] = self.create(image, self._image_size)

        return dict
