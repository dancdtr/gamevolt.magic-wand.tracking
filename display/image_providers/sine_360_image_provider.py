from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.image_provider import ImageProvider


class Sine360ImageProvider(ImageProvider):
    def __init__(self, base_png: str, image_size: int) -> None:
        super().__init__()

        base_image = self.load(base_png)

        self._image_library: dict[GestureType, PhotoImage] = {
            GestureType.WAVE_SINE_360_N: self.create(base_image, image_size, rotation_angle=0),
            GestureType.WAVE_SINE_360_E: self.create(base_image, image_size, rotation_angle=270),
            GestureType.WAVE_SINE_360_S: self.create(base_image, image_size, rotation_angle=180),
            GestureType.WAVE_SINE_360_W: self.create(base_image, image_size, rotation_angle=90),
            GestureType.WAVE_NEGATIVE_SINE_360_N: self.create(base_image, image_size, rotation_angle=0, flip_x=True),
            GestureType.WAVE_NEGATIVE_SINE_360_E: self.create(base_image, image_size, rotation_angle=270, flip_y=True),
            GestureType.WAVE_NEGATIVE_SINE_360_S: self.create(base_image, image_size, rotation_angle=180, flip_x=True),
            GestureType.WAVE_NEGATIVE_SINE_360_W: self.create(base_image, image_size, rotation_angle=90, flip_y=True),
        }

    def get_image_library(self) -> dict[GestureType, PhotoImage]:
        return self._image_library
