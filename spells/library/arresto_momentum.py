from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def arresto_momentum() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE}), required=True),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_SE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_SE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.8,
        max_total_duration_s=3.0,
        max_idle_gap_s=1,
        max_filler_duration_s=1,
        check_duration=True,
    )
