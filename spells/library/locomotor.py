from motion.direction.direction_type import DirectionType
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def get_locomotor(difficulty: SpellDifficultyType) -> SpellDefinition:
    return LOCOMOTOR


LOCOMOTOR = SpellDefinition(
    id="SP02",
    name="LOCOMOTOR",
    step_groups=[
        SpellStepGroup(
            name="Line_N",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=1 / 3,
            relative_duration=1 / 3,
        ),
        SpellStepGroup(
            name="Line_SW",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_S})),
                SpellStep(frozenset({DirectionType.MOVING_SW})),
                SpellStep(frozenset({DirectionType.MOVING_W})),
            ],
            relative_distance=1 / 3,
            relative_duration=1 / 3,
        ),
        SpellStepGroup(
            name="Line_E",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
            ],
            relative_distance=1 / 3,
            relative_duration=1 / 3,
        ),
    ],
    min_spell_steps=4,
    min_total_duration_s=0.8,
    max_total_duration_s=3.0,
    max_idle_gap_s=1,
    max_filler_duration_s=1,
    check_duration=True,
)
