from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def aparecium() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_W",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                ],
            ),
            SpellStepGroup(
                name="Squiggle_1",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                    SpellStep(frozenset({DirectionType.MOVING_SE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
            ),
            SpellStepGroup(
                name="Squiggle_2",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
            ),
            SpellStepGroup(
                name="Squiggle_3",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
            ),
            SpellStepGroup(
                name="Squiggle_4",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
            ),
            SpellStepGroup(
                name="Squiggle_5",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                ],
            ),
            SpellStepGroup(
                name="Squiggle_6",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE}), required=True),
                ],
            ),
        ],
        min_spell_steps=7,
        min_total_duration_s=1.5,
        max_total_duration_s=5,
        max_idle_gap_s=0.8,
        max_filler_duration_s=1,
    )
