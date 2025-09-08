from typing import Iterable

from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class DebugImageProvider(GestureImageProvider):
    def __init__(self, unknown_png: str, none_png: str, image_size: int) -> None:
        super().__init__()

        self._unknown_png = unknown_png
        self._none_png = none_png
        self._image_size = image_size

        self._image_library: dict[GestureType, PILImage] = {}

    def items(self) -> Iterable[tuple[GestureType, PILImage]]:
        return self._image_library.items()

    def load(self) -> None:
        unknown_img = load_image(self._unknown_png)
        none_img = load_image(self._none_png)

        self._image_library: dict[GestureType, PILImage] = {
            GestureType.UNKNOWN: self.create_variant(unknown_img, self._image_size),
            GestureType.NONE: self.create_variant(none_img, self._image_size),
        }
