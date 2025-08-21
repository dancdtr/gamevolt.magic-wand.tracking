from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.image_provider import ImageProvider


class CrookImageProvider(ImageProvider):
    def __init__(self, base_png: str, image_size: int) -> None:
        super().__init__()

        base_image = self.load(base_png)

        self._image_library: dict[GestureType, PhotoImage] = {
            GestureType.CROOK_N_CW: self.create(base_image, image_size, rotation_angle=0),
            GestureType.CROOK_E_CW: self.create(base_image, image_size, rotation_angle=270),
            GestureType.CROOK_S_CW: self.create(base_image, image_size, rotation_angle=180),
            GestureType.CROOK_W_CW: self.create(base_image, image_size, rotation_angle=90),
            GestureType.CROOK_N_CCW: self.create(base_image, image_size, rotation_angle=0, flip_x=True),
            GestureType.CROOK_E_CCW: self.create(base_image, image_size, rotation_angle=270, flip_x=True),
            GestureType.CROOK_S_CCW: self.create(base_image, image_size, rotation_angle=180, flip_x=True),
            GestureType.CROOK_W_CCW: self.create(base_image, image_size, rotation_angle=90, flip_x=True),
        }

    def get_image_library(self) -> dict[GestureType, PhotoImage]:
        return self._image_library
