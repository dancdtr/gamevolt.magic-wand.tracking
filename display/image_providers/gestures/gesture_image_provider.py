# display/image_providers/gestures/gesture_image_provider.py
from abc import ABC, abstractmethod

from PIL import Image
from PIL.Image import Image as PILImage

from classification.gesture_type import GestureType
from gamevolt.display.pil_image_provider import PILImageProvider


class GestureImageProvider(PILImageProvider[GestureType], ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def load(self) -> None: ...

    # util
    def create_variant(
        self,
        image_file: PILImage,
        size: int,
        rotation_angle: float = 0,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> PILImage:
        image = image_file.rotate(angle=0, expand=True)

        if flip_x:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        image = image.rotate(angle=rotation_angle, expand=True)
        image = image.resize((size, size), Image.Resampling.LANCZOS)

        if flip_y:
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        return image
