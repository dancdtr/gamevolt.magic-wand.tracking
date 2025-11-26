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
            name="Spell",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E})),
                SpellStep(frozenset({DirectionType.MOVING_NE}), required=True),
                SpellStep(frozenset({DirectionType.MOVING_E})),
                SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_E})),
                SpellStep(frozenset({DirectionType.MOVING_SW}), required=True),
            ],
            relative_distance=0.5,
            relative_duration=0.5,
        ),
        SpellStepGroup(
            name="Spell",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_W})),
                SpellStep(frozenset({DirectionType.MOVING_NW})),
                SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=0.5,
            relative_duration=0.5,
        ),
    ],
    min_spell_steps=4,
    max_total_duration_s=5.0,
    max_idle_gap_s=1.20,
    max_filler_duration_s=0.7,
)
