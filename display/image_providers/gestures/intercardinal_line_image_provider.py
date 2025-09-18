from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class IntercardinalLineImageProvider(GestureImageProvider):
    def load(self) -> None:
        base_image = load_image(self.image_path)

        self.image_library: dict[GestureType, PILImage] = {
            GestureType.LINE_NE: self.create_variant(base_image, self.image_size, rotation_angle=0),
            GestureType.LINE_SE: self.create_variant(base_image, self.image_size, rotation_angle=270),
            GestureType.LINE_SW: self.create_variant(base_image, self.image_size, rotation_angle=180),
            GestureType.LINE_NW: self.create_variant(base_image, self.image_size, rotation_angle=90),
        }
