from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def incendio() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
                ],
            ),
            SpellStepGroup(
                name="Line_SE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
                ],
            ),
            SpellStepGroup(
                name="Line_W",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NW, DirectionType.MOVING_W}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                ],
            ),
        ],
        min_spell_steps=3,
        min_total_duration_s=0.7,
        max_total_duration_s=2.5,
        max_idle_gap_s=0.6,
        max_filler_duration_s=0.5,
        pause_speed_threshold=0.04,
    )
