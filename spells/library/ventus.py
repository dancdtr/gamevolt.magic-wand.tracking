from motion.direction.direction_type import DirectionType
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup

VENTUS = SpellDefinition(
    id="SP69",
    name="NOX",
    step_groups=[
        SpellStepGroup(
            name="Line_SE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SE}), required=True),
            ],
            relative_distance=1 / 2,
            relative_duration=1 / 2,
        ),
        SpellStepGroup(
            name="Line_NE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_NE}), required=True),
            ],
            relative_distance=1 / 2,
            relative_duration=1 / 2,
        ),
    ],
    min_spell_steps=2,
    max_total_duration_s=10.0,
    max_idle_gap_s=1.20,
)


def get_ventus(difficulty: SpellDifficultyType) -> SpellDefinition:
    return VENTUS
