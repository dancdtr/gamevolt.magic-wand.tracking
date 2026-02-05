from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def alohomora() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Circle",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    SpellStep(frozenset({DirectionType.MOVING_NW})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
                relative_distance=3 / 5,
                relative_duration=3 / 5,
            ),
            SpellStepGroup(
                name="Line_S",
                steps=[
                    CORNER_PAUSE,
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE, DirectionType.MOVING_SW}), required=True),
                ],
                relative_distance=2 / 5,
                relative_duration=2 / 5,
            ),
        ],
        min_spell_steps=5,
        min_total_duration_s=1,
        max_total_duration_s=3.5,
        max_idle_gap_s=0.8,
        max_filler_duration_s=1,
        check_distance=False,
        check_duration=True,
        check_group_distance_ratio=False,
        check_group_duration_ratio=False,
        min_pre_pause_s=0.0,
        min_post_pause_s=0.0,
    )
