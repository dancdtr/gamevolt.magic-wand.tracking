from motion.direction.direction_type import DirectionType
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup

LUMOS_MAXIMA = SpellDefinition(
    id="SP28",
    name="LUMOS_MAXIMA",
    step_groups=[
        SpellStepGroup(
            name="Line_NE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_NE}), required=True),
                # SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=1 / 2,
            relative_duration=1 / 2,
        ),
        SpellStepGroup(
            name="Line_SE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SE}), required=True),
                # SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
            ],
            relative_distance=1 / 2,
            relative_duration=1 / 2,
        ),
    ],
    min_spell_steps=2,
    min_total_duration_s=0.5,
    max_total_duration_s=10.0,
    max_idle_gap_s=1.20,
    max_filler_duration_s=0.5,
    check_distance=False,
    check_duration=True,
    check_group_distance_ratio=False,
    check_group_duration_ratio=False,
)


def get_lumos_maxima(difficulty: SpellDifficultyType) -> SpellDefinition:
    return LUMOS_MAXIMA
