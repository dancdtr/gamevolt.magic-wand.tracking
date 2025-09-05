from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.image_provider import GestureImageProvider


class IntercardinalLineImageProvider(GestureImageProvider):
    def __init__(self, base_png: str, image_size: int) -> None:
        super().__init__()

        base_image = self.load(base_png)

        self._image_library: dict[GestureType, PhotoImage] = {
            GestureType.LINE_NE: self.create(base_image, image_size, rotation_angle=0),
            GestureType.LINE_SE: self.create(base_image, image_size, rotation_angle=270),
            GestureType.LINE_SW: self.create(base_image, image_size, rotation_angle=180),
            GestureType.LINE_NW: self.create(base_image, image_size, rotation_angle=90),
        }

    def image_library(self) -> dict[GestureType, PhotoImage]:
        return self._image_library
