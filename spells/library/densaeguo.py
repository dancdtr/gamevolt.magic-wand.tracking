from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def densaeguo() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Flick_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="U_Bend",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SW}), required=True),
                ],
                relative_distance=1 / 2,
                relative_duration=1 / 2,
            ),
            SpellStepGroup(
                name="Flick_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
        ],
        min_spell_steps=3,
        min_total_duration_s=0.7,
        max_total_duration_s=2.5,
        max_idle_gap_s=0.6,
        max_filler_duration_s=0.5,
        check_duration=True,
        pause_speed_threshold=0.04,
    )
