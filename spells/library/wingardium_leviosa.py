from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def wingardium_leviosa() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="ARC_180_CCW_START_W",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    CORNER_PAUSE,
                ],
                min_steps=2,
            ),
            SpellStepGroup(
                name="LINE_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.7,
        max_total_duration_s=4.0,
        max_idle_gap_s=1.2,
        max_filler_duration_s=1.2,
    )
