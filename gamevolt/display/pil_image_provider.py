# display/images/libraries/pil_image_provider.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, Iterable, TypeVar

from PIL import Image
from PIL.Image import Image as PILImage

from gamevolt.display.utils import recolour_region_by_threshold

T = TypeVar("T")

_THRESH = 230


class PILImageProvider(Generic[T], ABC):
    @abstractmethod
    def items(self) -> Iterable[tuple[T, PILImage]]: ...


# util
def load_image(path: str | Path) -> PILImage:
    with Image.open(path) as im:
        return im.convert("RGBA")


def recolour_icon(image: PILImage, colour: tuple[int, int, int]) -> PILImage:
    return recolour_region_by_threshold(image, colour, _THRESH, False)


def recolour_bg(image: PILImage, colour: tuple[int, int, int]) -> PILImage:
    return recolour_region_by_threshold(image, colour, _THRESH, True)
