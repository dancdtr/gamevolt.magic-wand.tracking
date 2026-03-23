from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class SpellRegistrySettings(SettingsBase):
    spells: list[tuple[int, str]]
