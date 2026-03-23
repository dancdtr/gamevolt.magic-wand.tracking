from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def flipendo() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_SW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE}), required=True),
                    CORNER_PAUSE,
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Line_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Line_NE",
                steps=[
                    # SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
                min_steps=2,
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Flick_SW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_N}), required=True),
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
        ],
        min_spell_steps=5,
        min_total_duration_s=0.7,
        max_total_duration_s=2.5,
        max_idle_gap_s=0.8,
        max_filler_duration_s=0.8,
        check_duration=True,
        pause_speed_threshold=0.04,
    )
