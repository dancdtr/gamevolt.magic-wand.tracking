from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from gamevolt.display.pil_image_provider import load_image


class Sine360ImageProvider(GestureImageProvider):
    def load(self) -> None:
        base_image = load_image(self.image_path)

        self.image_library: dict[GestureType, PILImage] = {
            GestureType.WAVE_SINE_360_N: self.create_variant(base_image, self.image_size, rotation_angle=0),
            GestureType.WAVE_SINE_360_E: self.create_variant(base_image, self.image_size, rotation_angle=270),
            GestureType.WAVE_SINE_360_S: self.create_variant(base_image, self.image_size, rotation_angle=180),
            GestureType.WAVE_SINE_360_W: self.create_variant(base_image, self.image_size, rotation_angle=90),
            GestureType.WAVE_NEGATIVE_SINE_360_N: self.create_variant(base_image, self.image_size, rotation_angle=0, flip_x=True),
            GestureType.WAVE_NEGATIVE_SINE_360_E: self.create_variant(base_image, self.image_size, rotation_angle=270, flip_y=True),
            GestureType.WAVE_NEGATIVE_SINE_360_S: self.create_variant(base_image, self.image_size, rotation_angle=180, flip_x=True),
            GestureType.WAVE_NEGATIVE_SINE_360_W: self.create_variant(base_image, self.image_size, rotation_angle=90, flip_y=True),
        }
