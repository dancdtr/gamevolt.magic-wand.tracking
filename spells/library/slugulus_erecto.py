from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def slugulus_erecto() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_SW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SW, DirectionType.MOVING_W})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_N",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_NW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_E})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.7,
        max_total_duration_s=3.5,
        max_idle_gap_s=0.4,
        max_filler_duration_s=1,
        check_duration=True,
    )
