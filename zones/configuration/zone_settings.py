from gamevolt.configuration.appsetting import appsetting
from spells.spell_type import SpellType


@appsetting
class ZoneSettings:
    id: str
    key: int
    spells: list[SpellType]
