from typing import Callable

from spells.library.locomotor import get_locomotor
from spells.library.revelio import get_revelio
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_type import SpellType

_SPELL_PROVIDERS: dict[SpellType, Callable[[SpellDifficultyType], SpellDefinition]] = {
    SpellType.REVELIO: get_revelio,
    SpellType.LOCOMOTOR: get_locomotor,
}


class SpellDefinitionFactory:

    def create(self, spell_type: SpellType, difficulty: SpellDifficultyType) -> SpellDefinition:
        provider = _SPELL_PROVIDERS.get(spell_type, None)

        if not provider:
            raise ValueError(f"No spell provider defined for type: '{spell_type.name}'.")

        return provider(difficulty)
