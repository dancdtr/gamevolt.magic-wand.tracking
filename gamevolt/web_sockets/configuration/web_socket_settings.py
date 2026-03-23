from __future__ import annotations

from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WebSocketSettings(SettingsBase):
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}/"
