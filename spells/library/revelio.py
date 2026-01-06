from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def revelio() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_N",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
                ],
                relative_distance=3 / 9,
                relative_duration=3 / 9,
            ),
            SpellStepGroup(
                name="Curve_270_CW_Start_E",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                ],
                relative_distance=4 / 9,
                relative_duration=4 / 9,
            ),
            SpellStepGroup(
                name="Line_SE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_E}), required=True),
                ],
                relative_distance=2 / 9,
                relative_duration=2 / 9,
            ),
        ],
        min_spell_steps=6,
        min_total_duration_s=0.8,
        max_total_duration_s=3.0,
        max_idle_gap_s=1,
        max_filler_duration_s=1,
        check_duration=True,
    )
