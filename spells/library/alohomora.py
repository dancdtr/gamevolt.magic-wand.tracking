from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def alohomora() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="cw_quarter_circle_start_n",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                ],
                relative_distance=3 / 5,
                relative_duration=3 / 5,
                min_steps=1,
            ),
            SpellStepGroup(
                name="cw_quarter_circle_start_e",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                ],
                relative_distance=3 / 5,
                relative_duration=3 / 5,
                min_steps=1,
            ),
            SpellStepGroup(
                name="cw_quarter_circle_start_s",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    SpellStep(frozenset({DirectionType.MOVING_NW})),
                ],
                min_steps=1,
                relative_distance=3 / 5,
                relative_duration=3 / 5,
            ),
            SpellStepGroup(
                name="cw_quarter_circle_start_w",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                ],
                min_steps=1,
                relative_distance=3 / 5,
                relative_duration=3 / 5,
            ),
            SpellStepGroup(
                name="Line_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    CORNER_PAUSE,
                    SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
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
    )
