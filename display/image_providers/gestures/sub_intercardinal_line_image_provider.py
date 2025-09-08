from typing import Iterable

from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class SubIntercardinalLineImageProvider(GestureImageProvider):
    def __init__(self, base_png: str, image_size: int) -> None:
        super().__init__()
        self._base_image = base_png
        self._image_size = image_size

        self._image_library: dict[GestureType, PILImage] = {}

    def items(self) -> Iterable[tuple[GestureType, PILImage]]:
        return self._image_library.items()

    def load(self) -> None:
        base_image = load_image(self._base_image)

        self._image_library: dict[GestureType, PILImage] = {
            GestureType.LINE_NNE: self.create_variant(base_image, self._image_size, rotation_angle=0),
            GestureType.LINE_ENE: self.create_variant(base_image, self._image_size, rotation_angle=270, flip_y=True),
            GestureType.LINE_ESE: self.create_variant(base_image, self._image_size, rotation_angle=270),
            GestureType.LINE_SSE: self.create_variant(base_image, self._image_size, rotation_angle=180, flip_x=True),
            GestureType.LINE_SSW: self.create_variant(base_image, self._image_size, rotation_angle=180),
            GestureType.LINE_WSW: self.create_variant(base_image, self._image_size, rotation_angle=90, flip_y=True),
            GestureType.LINE_WNW: self.create_variant(base_image, self._image_size, rotation_angle=90),
            GestureType.LINE_NNW: self.create_variant(base_image, self._image_size, rotation_angle=0, flip_x=True),
        }
