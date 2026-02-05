from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def slugulus_erecto() -> SpellDefinition:

    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="Line_S",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
                    CORNER_PAUSE,
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_SW",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_SW, DirectionType.MOVING_W})),
                    CORNER_PAUSE,
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_N",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N})),
                    CORNER_PAUSE,
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
            SpellStepGroup(
                name="Line_NW",
                steps=[
                    # (name says NW but allowed is NE/E; leaving as-is per your original)
                    SpellStep(frozenset({DirectionType.MOVING_NE, DirectionType.MOVING_E})),
                    # optional pause at end if you want a “final settle”
                    # corner_pause,
                ],
                relative_distance=1 / 4,
                relative_duration=1 / 4,
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.7,
        max_total_duration_s=2.5,
        # Keep general idle gap tighter now that pauses are explicit:
        max_idle_gap_s=0.20,
        # Filler is still allowed, but not massive.
        max_filler_duration_s=0.60,
        check_duration=True,
    )
