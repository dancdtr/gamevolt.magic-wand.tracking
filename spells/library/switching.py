from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def switching() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
                ],
                relative_distance=1 / 2,
                relative_duration=1 / 2,
            ),
            SpellStepGroup(
                name="LINE_E",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
                ],
                relative_distance=1 / 2,
                relative_duration=1 / 2,
            ),
        ],
        min_spell_steps=2,
        min_total_duration_s=0.7,
        max_total_duration_s=4.0,
        max_idle_gap_s=1.2,
        max_filler_duration_s=1.2,
        check_duration=True,
        min_pre_pause_s=0,
        min_post_pause_s=0,
    )
