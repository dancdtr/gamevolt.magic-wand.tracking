from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def colovaria() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Curve",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Line_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NW})),
                    SpellStep(frozenset({DirectionType.MOVING_W})),
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Line_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S, DirectionType.MOVING_E}), required=True),
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
        ],
        min_spell_steps=6,
        min_total_duration_s=0.8,
        max_total_duration_s=3.5,
        max_idle_gap_s=0.4,
        max_filler_duration_s=0.7,
        check_duration=True,
    )
