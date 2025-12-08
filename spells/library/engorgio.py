from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def engorgio() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_SE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_E}), required=True),
                ],
                relative_distance=1 / 2,
                relative_duration=1 / 2,
            ),
            SpellStepGroup(
                name="Line_NE",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SW, DirectionType.MOVING_W}), required=True),
                ],
                relative_distance=1 / 2,
                relative_duration=1 / 2,
            ),
        ],
        min_spell_steps=2,
        min_total_duration_s=0.7,
        max_total_duration_s=2,
        max_idle_gap_s=0.5,
        max_filler_duration_s=0.5,
    )
