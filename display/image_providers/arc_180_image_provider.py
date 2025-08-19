from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.image_provider import ImageProvider


class Arc180ImageProvider(ImageProvider):
    def __init__(self, base_png: str, image_size: int) -> None:
        super().__init__()

        base_image = self.load(base_png)

        self._image_library: dict[GestureType, PhotoImage] = {
            GestureType.ARC_180_CW_START_N: self.create(base_image, image_size, rotation_angle=0),
            GestureType.ARC_180_CW_START_E: self.create(base_image, image_size, rotation_angle=270),
            GestureType.ARC_180_CW_START_S: self.create(base_image, image_size, rotation_angle=180),
            GestureType.ARC_180_CW_START_W: self.create(base_image, image_size, rotation_angle=90),
            GestureType.ARC_180_CCW_START_N: self.create(base_image, image_size, rotation_angle=0, flip_x=True),
            GestureType.ARC_180_CCW_START_E: self.create(base_image, image_size, rotation_angle=270, flip_x=True),
            GestureType.ARC_180_CCW_START_S: self.create(base_image, image_size, rotation_angle=180, flip_x=True),
            GestureType.ARC_180_CCW_START_W: self.create(base_image, image_size, rotation_angle=90, flip_x=True),
        }

    def get_image_library(self) -> dict[GestureType, PhotoImage]:
        return self._image_library
