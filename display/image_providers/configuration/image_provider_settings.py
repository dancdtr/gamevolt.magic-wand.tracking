from gamevolt.configuration.appsetting import appsetting
from gamevolt.io import bundled_path


@appsetting
class ImageProviderSettings:
    assets_dir: list[str]
    image_size: int
    bg_colour: tuple[int, int, int]
    icon_colour: tuple[int, int, int]

    @property
    def bundled_path(self) -> str:
        return str(bundled_path(*self.assets_dir))
