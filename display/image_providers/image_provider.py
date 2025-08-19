from abc import ABC, abstractmethod

from PIL import Image
from PIL.ImageFile import ImageFile
from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType


class ImageProvider(ABC):
    def __init__(self, assets_dir: str = "./display/images/primitives") -> None:
        super().__init__()

        self._assets_dir = assets_dir

    @abstractmethod
    def get_image_library(self) -> dict[GestureType, PhotoImage]: ...

    def get_image(self, gesture_type: GestureType) -> PhotoImage | None:
        return self.get_image_library().get(gesture_type)

    def load(self, img_path: str) -> ImageFile:
        return Image.open(img_path)

    def create(self, img: ImageFile, size: int, rotation_angle: float = 0, flip_x: bool = False, flip_y: bool = False) -> PhotoImage:
        image = img.rotate(angle=0, expand=True)

        if flip_x:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        image = image.rotate(angle=rotation_angle, expand=True)
        image = image.resize((size, size), Image.Resampling.LANCZOS)

        if flip_y:
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        return PhotoImage(image)
