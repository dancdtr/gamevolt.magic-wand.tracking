from PIL import Image
from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class UnknownImageProvider(GestureImageProvider):
    def load(self) -> None:
        base_image = load_image(self.image_path)
        size = (self.image_size, self.image_size)

        self.image_library: dict[GestureType, PILImage] = {
            GestureType.UNKNOWN: base_image.resize(size, Image.Resampling.LANCZOS),
        }
