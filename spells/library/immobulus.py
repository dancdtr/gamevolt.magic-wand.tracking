from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def immobulus() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_NW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_W, DirectionType.MOVING_NW}), required=True),
                    CORNER_PAUSE,
                ],
                min_steps=1,
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Line_E",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E, DirectionType.MOVING_SE})),
                    CORNER_PAUSE,
                ],
                min_steps=1,
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Line_SW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SW}), required=True),
                ],
                min_steps=1,
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
        ],
        min_spell_steps=3,
        min_total_duration_s=0.7,
        max_total_duration_s=2,
        max_idle_gap_s=1,
        max_filler_duration_s=1,
        check_duration=True,
    )
