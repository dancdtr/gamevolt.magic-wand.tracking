from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def herbivicius() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="LINE_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE}), required=True),
                ],
            ),
            SpellStepGroup(
                name="ARC_180_CCW_START_W",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                ],
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.7,
        max_total_duration_s=4.0,
        max_idle_gap_s=0.8,
        max_filler_duration_s=0.7,
    )
