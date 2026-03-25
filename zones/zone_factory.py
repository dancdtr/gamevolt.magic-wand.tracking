from logging import Logger

from spells.spell_type import SpellType
from zones.zone import Zone


class ZoneFactory:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def create(self, id: str, spell_types: list[SpellType]) -> Zone:
        return Zone(
            logger=self._logger,
            id=id,
            spell_types=spell_types,
        )
