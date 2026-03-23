from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def expecto_patronum() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Flick_1",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    SpellStep(frozenset({DirectionType.MOVING_NW})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                ],
                min_steps=3,
                relative_distance=1,
                relative_duration=1,
            ),
            SpellStepGroup(
                name="Flick_2",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SW, DirectionType.MOVING_W}), required=True),
                ],
                min_steps=3,
                relative_distance=1,
                relative_duration=1,
            ),
        ],
        min_spell_steps=6,
        min_total_duration_s=0.7,
        max_total_duration_s=2.5,
        max_idle_gap_s=0.8,
        max_filler_duration_s=0.8,
        check_duration=True,
        pause_speed_threshold=0.04,
    )
