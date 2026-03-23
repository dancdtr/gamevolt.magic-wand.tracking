from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.io.utils import bundled_path


@dataclass
class ImageProviderSettings(SettingsBase):
    assets_dir: list[str]
    image_size: int
    bg_colour: tuple[int, int, int]
    icon_colour: tuple[int, int, int]

    @property
    def bundled_path(self) -> str:
        return bundled_path(*self.assets_dir)
