from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def piertotum_locomotor() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_SW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_W, DirectionType.MOVING_SW}), required=True),
                ],
            ),
            SpellStepGroup(
                name="Line_W",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                ],
            ),
            SpellStepGroup(
                name="Line_N",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE}), required=True),
                ],
            ),
        ],
        min_spell_steps=3,
        min_total_duration_s=0.8,
        max_total_duration_s=2,
        max_idle_gap_s=0.4,
        max_filler_duration_s=0.8,
    )
