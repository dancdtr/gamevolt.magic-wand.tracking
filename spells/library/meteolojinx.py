from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def meteolojinx() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="ARC_180_CCW_START_E",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NW})),
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    CORNER_PAUSE,
                ],
                # min_steps=3,
            ),
            SpellStepGroup(
                name="ARC_180_CW_START_W",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                ],
                # min_steps=3,
            ),
        ],
        min_spell_steps=6,
        min_total_duration_s=0.7,
        max_total_duration_s=3.0,
        max_idle_gap_s=2,
        max_filler_duration_s=2,
    )
