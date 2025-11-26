from motion.direction.direction_type import DirectionType
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup

ALOHOMORA = SpellDefinition(
    id="SP01",
    name="ALOHOMORA",
    step_groups=[
        SpellStepGroup(
            name="Circle",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E})),
                SpellStep(frozenset({DirectionType.MOVING_SE}), required=True),
                SpellStep(frozenset({DirectionType.MOVING_S})),
                SpellStep(frozenset({DirectionType.MOVING_SW})),
                SpellStep(frozenset({DirectionType.MOVING_W})),
                SpellStep(frozenset({DirectionType.MOVING_NW}), required=True),
                SpellStep(frozenset({DirectionType.MOVING_N})),
                SpellStep(frozenset({DirectionType.MOVING_NE})),
                SpellStep(frozenset({DirectionType.MOVING_E})),
            ],
            relative_distance=3 / 5,
            relative_duration=3 / 5,
        ),
        SpellStepGroup(
            name="Line_S",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE}), required=True),
            ],
            relative_distance=2 / 5,
            relative_duration=2 / 5,
        ),
    ],
    min_spell_steps=7,
    min_total_duration_s=0.7,
    max_total_duration_s=4.0,
    max_idle_gap_s=1.20,
    max_filler_duration_s=1,
    check_distance=False,
    check_duration=True,
    check_group_distance_ratio=False,
    check_group_duration_ratio=False,
)


def get_alohomora(difficulty: SpellDifficultyType) -> SpellDefinition:
    return ALOHOMORA
