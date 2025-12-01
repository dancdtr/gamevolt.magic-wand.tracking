from motion.direction.direction_type import DirectionType
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def get_none_spell(difficulty: SpellDifficultyType) -> SpellDefinition:
    return NONE_SPELL


NONE_SPELL = SpellDefinition(
    id="SP000",
    name="NONE",
    step_groups=[],
    min_spell_steps=1,
)
