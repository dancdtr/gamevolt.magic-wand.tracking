from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class HookImageProvider(GestureImageProvider):
    def __init__(self, image_path: str, image_size: int) -> None:
        super().__init__(image_path, image_size)

    def load(self) -> None:
        base_image = load_image(self.image_path)

        self.image_library: dict[GestureType, PILImage] = {
            GestureType.HOOK_N_CW: self.create_variant(base_image, self.image_size, rotation_angle=0),
            GestureType.HOOK_E_CW: self.create_variant(base_image, self.image_size, rotation_angle=270),
            GestureType.HOOK_S_CW: self.create_variant(base_image, self.image_size, rotation_angle=180),
            GestureType.HOOK_W_CW: self.create_variant(base_image, self.image_size, rotation_angle=90),
            GestureType.HOOK_N_CCW: self.create_variant(base_image, self.image_size, rotation_angle=0, flip_x=True),
            GestureType.HOOK_E_CCW: self.create_variant(base_image, self.image_size, rotation_angle=270, flip_x=True),
            GestureType.HOOK_S_CCW: self.create_variant(base_image, self.image_size, rotation_angle=180, flip_x=True),
            GestureType.HOOK_W_CCW: self.create_variant(base_image, self.image_size, rotation_angle=90, flip_x=True),
        }
