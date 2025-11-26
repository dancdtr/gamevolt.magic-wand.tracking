from motion.direction.direction_type import DirectionType
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def get_revelio(difficulty: SpellDifficultyType) -> SpellDefinition:
    return REVELIO_HARD
    if difficulty is SpellDifficultyType.FORGIVING:
        return REVELIO_EASY
    if difficulty is SpellDifficultyType.STRICT:
        return REVELIO_HARD

    raise ValueError(f"No spell definition for Revelio difficulty: {difficulty.name}")


REVELIO_HARD = SpellDefinition(
    id="SP001",
    name="REVELIO",
    step_groups=[
        SpellStepGroup(
            name="Line_N",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=3 / 9,
            relative_duration=3 / 9,
        ),
        SpellStepGroup(
            name="Curve_270_CW_Start_E",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_NE})),
                SpellStep(frozenset({DirectionType.MOVING_E})),
                SpellStep(frozenset({DirectionType.MOVING_SE})),
                SpellStep(frozenset({DirectionType.MOVING_S})),
                SpellStep(frozenset({DirectionType.MOVING_SW})),
                SpellStep(frozenset({DirectionType.MOVING_W})),
            ],
            relative_distance=4 / 9,
            relative_duration=4 / 9,
        ),
        SpellStepGroup(
            name="Line_SE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SE}), required=True),
            ],
            relative_distance=2 / 9,
            relative_duration=2 / 9,
        ),
    ],
    min_spell_steps=4,
    max_total_duration_s=5.0,
    max_idle_gap_s=1.20,
    max_filler_duration_s=0.35,
)

REVELIO_EASY = SpellDefinition(
    id="SP01",
    name="REVELIO",
    step_groups=[
        SpellStepGroup(
            name="Line_N",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=3 / 9,
            relative_duration=3 / 9,
        ),
        SpellStepGroup(
            name="Arc_180_CW_Start_E",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_NE})),
                SpellStep(frozenset({DirectionType.MOVING_E, DirectionType.MOVING_NE, DirectionType.MOVING_SE}), 0.03, required=True),
                SpellStep(frozenset({DirectionType.MOVING_SE})),
                SpellStep(frozenset({DirectionType.MOVING_S})),
            ],
            relative_distance=2 / 9,
            relative_duration=2 / 9,
        ),
        SpellStepGroup(
            name="Arc_180_CW_Start_W",
            steps=[
                # SpellStep(frozenset({DirectionType.MOVING_SW})),
                SpellStep(frozenset({DirectionType.MOVING_W, DirectionType.MOVING_NW, DirectionType.MOVING_SW}), 0.03, required=True),
                SpellStep(frozenset({DirectionType.MOVING_SW})),
            ],
            relative_distance=2 / 9,
            relative_duration=2 / 9,
        ),
        SpellStepGroup(
            name="Line_SE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SE}), required=True),
            ],
            relative_distance=2 / 9,
            relative_duration=2 / 9,
        ),
    ],
    min_spell_steps=5,
    max_total_duration_s=5.0,
    max_idle_gap_s=1.20,
)
