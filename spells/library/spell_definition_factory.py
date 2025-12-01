from typing import Callable

from spells.library.alohomora import get_alohomora
from spells.library.incendio import get_incendio
from spells.library.locomotor import get_locomotor
from spells.library.lumos_maxima import get_lumos_maxima
from spells.library.none import get_none_spell
from spells.library.revelio import get_revelio
from spells.library.rictumsempra import get_rictumsempra
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.library.ventus import get_ventus
from spells.library.wingardium_leviosa import get_wingardium_leviosa
from spells.spell_definition import SpellDefinition
from spells.spell_type import SpellType

_SPELL_PROVIDERS: dict[SpellType, Callable[[SpellDifficultyType], SpellDefinition]] = {
    SpellType.NONE: get_none_spell,
    SpellType.REVELIO: get_revelio,
    SpellType.LOCOMOTOR: get_locomotor,
    SpellType.LUMOS_MAXIMA: get_lumos_maxima,
    SpellType.VENTUS: get_ventus,
    SpellType.INCENDIO: get_incendio,
    SpellType.ALOHOMORA: get_alohomora,
    SpellType.WINGARDIUM_LEVIOSA: get_wingardium_leviosa,
    SpellType.RICTUMSEMPRA: get_rictumsempra,
}


class SpellDefinitionFactory:
    def create_spells(
        self, spell_types: list[SpellType], difficulty: SpellDifficultyType = SpellDifficultyType.FORGIVING
    ) -> list[SpellDefinition]:
        return [self.create_spell(spell_type, difficulty) for spell_type in spell_types]

    def create_spell(self, spell_type: SpellType, difficulty: SpellDifficultyType) -> SpellDefinition:
        provider = _SPELL_PROVIDERS.get(spell_type, None)

        if not provider:
            raise ValueError(f"No spell provider defined for type: '{spell_type.name}'.")

        return provider(difficulty)
