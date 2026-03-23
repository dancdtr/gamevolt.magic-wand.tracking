from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def reparo() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="FLICK_1",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NW})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                ],
                min_steps=2,
                relative_distance=1,
                relative_duration=1,
            ),
            SpellStepGroup(
                name="FLICK_2",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    SpellStep(frozenset({DirectionType.MOVING_NW})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
                min_steps=2,
                relative_distance=1,
                relative_duration=1,
            ),
        ],
        min_spell_steps=5,
        min_total_duration_s=0.7,
        max_total_duration_s=2,
        max_idle_gap_s=0.4,
        max_filler_duration_s=0.6,
        check_duration=True,
    )
