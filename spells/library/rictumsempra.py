from motion.direction.direction_type import DirectionType
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def get_rictumsempra(difficulty: SpellDifficultyType) -> SpellDefinition:
    return RICTUMSEMPRA


RICTUMSEMPRA = SpellDefinition(
    id="SP001",
    name="RICTUMSEMPRA",
    step_groups=[
        SpellStepGroup(
            name="Step1",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E})),
                SpellStep(frozenset({DirectionType.MOVING_NE}), required=True),
                SpellStep(frozenset({DirectionType.MOVING_E})),
                SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_E})),
            ],
            relative_distance=5 / 8,
            relative_duration=5 / 8,
        ),
        SpellStepGroup(
            name="Step2",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SW}), required=True),
            ],
            relative_distance=2 / 8,
            relative_duration=2 / 8,
        ),
        SpellStepGroup(
            name="Step3",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_W})),
                SpellStep(frozenset({DirectionType.MOVING_NW})),
                SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=1 / 8,
            relative_duration=1 / 8,
        ),
    ],
    min_spell_steps=4,
    max_total_duration_s=5.0,
    max_idle_gap_s=1.20,
    max_filler_duration_s=0.7,
)
