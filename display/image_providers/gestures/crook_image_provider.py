from typing import Iterable

from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class CrookImageProvider(GestureImageProvider):
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
            GestureType.CROOK_N_CW: self.create_variant(base_image, self._image_size, rotation_angle=0),
            GestureType.CROOK_E_CW: self.create_variant(base_image, self._image_size, rotation_angle=270),
            GestureType.CROOK_S_CW: self.create_variant(base_image, self._image_size, rotation_angle=180),
            GestureType.CROOK_W_CW: self.create_variant(base_image, self._image_size, rotation_angle=90),
            GestureType.CROOK_N_CCW: self.create_variant(base_image, self._image_size, rotation_angle=0, flip_x=True),
            GestureType.CROOK_E_CCW: self.create_variant(base_image, self._image_size, rotation_angle=270, flip_x=True),
            GestureType.CROOK_S_CCW: self.create_variant(base_image, self._image_size, rotation_angle=180, flip_x=True),
            GestureType.CROOK_W_CCW: self.create_variant(base_image, self._image_size, rotation_angle=90, flip_x=True),
        }
