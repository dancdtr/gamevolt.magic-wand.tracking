from motion.direction.direction_type import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def colloportus() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_E",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Line_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_N",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_W}), required=True),
                ],
                relative_distance=1 / 3,
                relative_duration=1 / 3,
            ),
            SpellStepGroup(
                name="Line_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S})),
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
        ],
        min_spell_steps=3,
        min_total_duration_s=0.8,
        max_total_duration_s=2,
        max_idle_gap_s=0.4,
        max_filler_duration_s=0.8,
        check_duration=True,
    )
