from motion.direction.direction_type import DirectionType
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup

INCENDIO = SpellDefinition(
    id="SP22",
    name="INCENDIO",
    step_groups=[
        SpellStepGroup(
            name="Line_NE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=1 / 3,
            relative_duration=1 / 3,
        ),
        SpellStepGroup(
            name="Line_SE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
            ],
            relative_distance=1 / 3,
            relative_duration=1 / 3,
        ),
        SpellStepGroup(
            name="Line_W",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_W, DirectionType.MOVING_NW}), required=True),
                SpellStep(
                    frozenset({DirectionType.MOVING_SW}),
                ),
            ],
            relative_distance=1 / 3,
            relative_duration=1 / 3,
        ),
    ],
    min_spell_steps=3,
    min_total_duration_s=0.5,
    max_total_duration_s=10.0,
    max_idle_gap_s=1.20,
    max_filler_duration_s=0.5,
    check_distance=False,
    check_duration=True,
    check_group_distance_ratio=False,
    check_group_duration_ratio=False,
    min_pre_pause_s=0.15,
    min_post_pause_s=0.15,
    pause_speed_threshold=0.04,
)


def get_incendio(difficulty: SpellDifficultyType) -> SpellDefinition:
    return INCENDIO
