from __future__ import annotations

from logging import Logger

from spells.configuration.spell_registry_settings import SpellRegistrySettings
from spells.spell import Spell
from spells.spell_type import SpellType


class SpellRegistry:
    def __init__(self, logger: Logger, settings: SpellRegistrySettings) -> None:
        self._logger = logger

        spells: list[Spell] = []
        spells_by_id: dict[int, Spell] = {}
        spells_by_name: dict[str, Spell] = {}
        spells_by_type: dict[SpellType, Spell] = {}

        for spell_id, spell_name in settings.spells:
            try:
                spell_type = SpellType[spell_name.upper()]
            except KeyError as ex:
                raise ValueError(f"Unknown spell type in settings: '{spell_name}'") from ex

            spell = Spell(spell_id, spell_type)

            if spell.id in spells_by_id:
                raise ValueError(f"Duplicate spell id in settings: {spell.id}")

            if spell.name.casefold() in spells_by_name:
                raise ValueError(f"Duplicate spell name in settings: '{spell.name}'")

            if spell.type in spells_by_type:
                raise ValueError(f"Duplicate spell type in settings: '{spell.type.name}'")

            spells.append(spell)
            spells_by_id[spell.id] = spell
            spells_by_name[spell.name.casefold()] = spell
            spells_by_type[spell.type] = spell

        self._items = spells
        self._spells_by_id = spells_by_id
        self._spells_by_name = spells_by_name
        self._spells_by_type = spells_by_type

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    @property
    def items(self) -> list[Spell]:
        return list(self._items)

    @property
    def names(self) -> list[str]:
        return [spell.name for spell in self._items]

    @property
    def long_names(self) -> list[str]:
        return [spell.long_name for spell in self._items]

    @property
    def ids(self) -> list[int]:
        return [spell.id for spell in self._items]

    @property
    def count(self) -> int:
        return len(self._items)

    def get_default(self) -> Spell:
        spell = self._spells_by_type.get(SpellType.NONE)
        if spell is not None:
            return spell

        self._logger.warning("No SpellType.NONE found in registry; returning fallback default.")
        return Spell(0, SpellType.NONE)

    def get_by_id(self, spell_id: int) -> Spell:
        spell = self._spells_by_id.get(spell_id)
        if spell is None:
            self._logger.error(f"No spell defined with id: {spell_id}!")
            return self.get_default()

        return spell

    def get_by_name(self, name: str) -> Spell:
        spell = self._spells_by_name.get(name.casefold())
        if spell is None:
            self._logger.error(f"No spell defined with name: '{name}'!")
            return self.get_default()

        return spell

    def get_by_type(self, spell_type: SpellType) -> Spell:
        spell = self._spells_by_type.get(spell_type)
        if spell is None:
            self._logger.error(f"No spell defined for type: {spell_type}!")
            return self.get_default()

        return spell

    def try_get_by_id(self, spell_id: int) -> Spell | None:
        return self._spells_by_id.get(spell_id)

    def try_get_by_name(self, name: str) -> Spell | None:
        return self._spells_by_name.get(name.casefold())

    def try_get_by_type(self, spell_type: SpellType) -> Spell | None:
        return self._spells_by_type.get(spell_type)
