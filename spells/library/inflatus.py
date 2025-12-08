from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def inflatus() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="ARC_180_CW_START_W",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
        ],
        min_spell_steps=3,
        min_total_duration_s=0.8,
        max_total_duration_s=3.0,
        max_idle_gap_s=0.3,
        max_filler_duration_s=0.6,
        check_duration=True,
    )
