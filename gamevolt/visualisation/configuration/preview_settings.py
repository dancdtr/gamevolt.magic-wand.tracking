from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class RootSettings(SettingsBase):
    title: str
    width: int
    height: int
    buffer: int

    @property
    def geometry(self) -> str:
        return f"{self.width}x{self.height}+{self.buffer}+{self.buffer}"
