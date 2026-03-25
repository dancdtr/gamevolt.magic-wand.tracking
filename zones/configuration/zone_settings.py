from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from spells.spell_type import SpellType


@dataclass
class ZoneSettings(SettingsBase):
    id: str
    spells: list[SpellType]
