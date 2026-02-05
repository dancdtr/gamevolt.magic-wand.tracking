from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def rictumsempra() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Step1",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E})),
                    SpellStep(frozenset({DirectionType.MOVING_NE})),
                    SpellStep(frozenset({DirectionType.MOVING_E, DirectionType.MOVING_SE})),
                ],
                relative_distance=5 / 8,
                relative_duration=5 / 8,
            ),
            SpellStepGroup(
                name="Step2",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SW})),
                    SpellStep(frozenset({DirectionType.MOVING_W}), required=True),
                ],
                relative_distance=2 / 8,
                relative_duration=2 / 8,
            ),
            SpellStepGroup(
                name="Step3",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_NW})),
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    SpellStep(frozenset({DirectionType.MOVING_NE}), required=True),
                ],
                relative_distance=1 / 8,
                relative_duration=1 / 8,
            ),
        ],
        min_spell_steps=5,
        max_total_duration_s=3.0,
        min_total_duration_s=0.7,
        max_idle_gap_s=0.8,
        max_filler_duration_s=0.7,
    )
