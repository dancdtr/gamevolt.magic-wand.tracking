from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.image_provider import ImageProvider


class DebugImageProvider(ImageProvider):
    def __init__(self, unknown_png: str, none_png: str, image_size: int) -> None:
        super().__init__()

        unknown_img = self.load(unknown_png)
        none_img = self.load(none_png)

        self._image_library: dict[GestureType, PhotoImage] = {
            GestureType.UNKNOWN: self.create(unknown_img, image_size),
            GestureType.NONE: self.create(none_img, image_size),
        }

    def get_image_library(self) -> dict[GestureType, PhotoImage]:
        return self._image_library
