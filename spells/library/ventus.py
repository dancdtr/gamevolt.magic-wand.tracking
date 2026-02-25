from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def ventus() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_SE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
                ],
            ),
            SpellStepGroup(
                name="Line_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
                ],
            ),
        ],
        min_spell_steps=2,
        max_total_duration_s=3,
        min_total_duration_s=0.7,
        max_idle_gap_s=0.5,
    )
