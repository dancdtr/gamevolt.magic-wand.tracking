from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.image_provider import ImageProvider


class InverseHookImageProvider(ImageProvider):
    def __init__(self, base_png: str, image_size: int) -> None:
        super().__init__()

        base_image = self.load(base_png)

        self._image_library: dict[GestureType, PhotoImage] = {
            GestureType.INVERSE_HOOK_N_CW: self.create(base_image, image_size, rotation_angle=0, flip_x=True),
            GestureType.INVERSE_HOOK_E_CW: self.create(base_image, image_size, rotation_angle=270, flip_x=True),
            GestureType.INVERSE_HOOK_S_CW: self.create(base_image, image_size, rotation_angle=180, flip_x=True),
            GestureType.INVERSE_HOOK_W_CW: self.create(base_image, image_size, rotation_angle=90, flip_x=True),
            GestureType.INVERSE_HOOK_N_CCW: self.create(base_image, image_size, rotation_angle=0),
            GestureType.INVERSE_HOOK_E_CCW: self.create(base_image, image_size, rotation_angle=270),
            GestureType.INVERSE_HOOK_S_CCW: self.create(base_image, image_size, rotation_angle=180),
            GestureType.INVERSE_HOOK_W_CCW: self.create(base_image, image_size, rotation_angle=90),
        }

    def get_image_library(self) -> dict[GestureType, PhotoImage]:
        return self._image_library
