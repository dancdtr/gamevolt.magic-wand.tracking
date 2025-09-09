from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class CardinalLineImageProvider(GestureImageProvider):
    def __init__(self, image_path: str, image_size: int) -> None:
        super().__init__(image_path, image_size)

    def load(self) -> None:
        base_image = load_image(self.image_path)

        if base_image:
            print(f"found base image: '{base_image}' at '{self.image_path}'")
        else:
            print(f"failed to find base image: '{base_image}'  at '{self.image_path}'")

        self.image_library: dict[GestureType, PILImage] = {
            GestureType.LINE_N: self.create_variant(base_image, self.image_size, rotation_angle=0),
            GestureType.LINE_E: self.create_variant(base_image, self.image_size, rotation_angle=270),
            GestureType.LINE_S: self.create_variant(base_image, self.image_size, rotation_angle=180),
            GestureType.LINE_W: self.create_variant(base_image, self.image_size, rotation_angle=90),
        }
