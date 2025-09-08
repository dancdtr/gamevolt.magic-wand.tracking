from dataclasses import dataclass


@dataclass
class ImageProviderSettings:
    assets_dir: str
    image_size: int
    bg_colour: tuple[int, int, int]
    icon_colour: tuple[int, int, int]
