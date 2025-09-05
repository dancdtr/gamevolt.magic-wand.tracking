from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.image_provider import GestureImageProvider


class SubIntercardinalLineImageProvider(GestureImageProvider):
    def __init__(self, base_png: str, image_size: int) -> None:
        super().__init__()

        base_image = self.load(base_png)

        self._image_library: dict[GestureType, PhotoImage] = {
            GestureType.LINE_NNE: self.create(base_image, image_size, rotation_angle=0),
            GestureType.LINE_ENE: self.create(base_image, image_size, rotation_angle=270, flip_y=True),
            GestureType.LINE_ESE: self.create(base_image, image_size, rotation_angle=270),
            GestureType.LINE_SSE: self.create(base_image, image_size, rotation_angle=180, flip_x=True),
            GestureType.LINE_SSW: self.create(base_image, image_size, rotation_angle=180),
            GestureType.LINE_WSW: self.create(base_image, image_size, rotation_angle=90, flip_y=True),
            GestureType.LINE_WNW: self.create(base_image, image_size, rotation_angle=90),
            GestureType.LINE_NNW: self.create(base_image, image_size, rotation_angle=0, flip_x=True),
        }

    def image_library(self) -> dict[GestureType, PhotoImage]:
        return self._image_library
