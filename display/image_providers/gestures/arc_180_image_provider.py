from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class Arc180ImageProvider(GestureImageProvider):
    def load(self) -> None:
        base_image = load_image(self.image_path)

        self.image_library: dict[GestureType, PILImage] = {
            GestureType.ARC_180_CW_START_N: self.create_variant(base_image, self.image_size, rotation_angle=0),
            GestureType.ARC_180_CW_START_E: self.create_variant(base_image, self.image_size, rotation_angle=270),
            GestureType.ARC_180_CW_START_S: self.create_variant(base_image, self.image_size, rotation_angle=180),
            GestureType.ARC_180_CW_START_W: self.create_variant(base_image, self.image_size, rotation_angle=90),
            GestureType.ARC_180_CCW_START_N: self.create_variant(base_image, self.image_size, rotation_angle=0, flip_x=True),
            GestureType.ARC_180_CCW_START_E: self.create_variant(base_image, self.image_size, rotation_angle=270, flip_x=True),
            GestureType.ARC_180_CCW_START_S: self.create_variant(base_image, self.image_size, rotation_angle=180, flip_x=True),
            GestureType.ARC_180_CCW_START_W: self.create_variant(base_image, self.image_size, rotation_angle=90, flip_x=True),
        }
