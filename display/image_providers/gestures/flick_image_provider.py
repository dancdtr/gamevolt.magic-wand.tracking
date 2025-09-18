from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class FlickImageProvider(GestureImageProvider):
    def load(self) -> None:
        base_image = load_image(self.image_path)

        self.image_library: dict[GestureType, PILImage] = {
            GestureType.FLICK_CW_NE: self.create_variant(base_image, self.image_size, rotation_angle=0),
            GestureType.FLICK_CW_SE: self.create_variant(base_image, self.image_size, rotation_angle=270),
            GestureType.FLICK_CW_SW: self.create_variant(base_image, self.image_size, rotation_angle=180),
            GestureType.FLICK_CW_NW: self.create_variant(base_image, self.image_size, rotation_angle=90),
            GestureType.FLICK_CCW_NE: self.create_variant(base_image, self.image_size, rotation_angle=270, flip_x=True),
            GestureType.FLICK_CCW_SE: self.create_variant(base_image, self.image_size, rotation_angle=180, flip_x=True),
            GestureType.FLICK_CCW_SW: self.create_variant(base_image, self.image_size, rotation_angle=90, flip_x=True),
            GestureType.FLICK_CCW_NW: self.create_variant(base_image, self.image_size, rotation_angle=0, flip_x=True),
        }
