from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def lumos_maxima() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE}), required=True),
                ],
            ),
            SpellStepGroup(
                name="Line_SE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE}), required=True),
                ],
            ),
        ],
        min_spell_steps=2,
        min_total_duration_s=0.7,
        max_total_duration_s=2.5,
        max_idle_gap_s=0.9,
        max_filler_duration_s=0.6,
        pause_speed_threshold=0.04,
    )
