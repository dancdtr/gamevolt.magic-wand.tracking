from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def cantis() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Circle",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
            ),
            SpellStepGroup(
                name="UpperArm",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
                ],
            ),
            SpellStepGroup(
                name="Flick",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_E}), required=True),
                ],
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.8,
        max_total_duration_s=3.5,
        max_idle_gap_s=0.8,
        max_filler_duration_s=1,
    )
