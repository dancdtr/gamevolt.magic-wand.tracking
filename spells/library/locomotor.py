from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def locomotor() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_N",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
                    CORNER_PAUSE,
                ],
            ),
            SpellStepGroup(
                name="Line_SW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SW}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    CORNER_PAUSE,
                ],
            ),
            SpellStepGroup(
                name="Line_E",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
                ],
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.8,
        max_total_duration_s=3.0,
        max_idle_gap_s=1,
        max_filler_duration_s=1,
    )
