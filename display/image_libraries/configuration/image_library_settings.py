from dataclasses import dataclass


@dataclass
class ImageLibrarySettings:
    assets_dir: str
    image_size: int
