from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def pepper_breath() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Flick_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                ],
            ),
            SpellStepGroup(
                name="Flick_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
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
