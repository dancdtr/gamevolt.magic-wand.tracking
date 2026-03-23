from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def silencio() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="ARC_180_CCW_START_W",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    SpellStep(frozenset({DirectionType.MOVING_NW, DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    CORNER_PAUSE,
                ],
                min_steps=2,
                relative_distance=3 / 4,
                relative_duration=3 / 4,
            ),
            SpellStepGroup(
                name="LINE_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE, DirectionType.MOVING_SW}), required=True),
                ],
                min_steps=1,
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.7,
        max_total_duration_s=4.0,
        max_idle_gap_s=1.2,
        max_filler_duration_s=1.3,
        check_duration=True,
        min_pre_pause_s=0,
        min_post_pause_s=0,
    )
