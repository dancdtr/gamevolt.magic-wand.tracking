from motion.direction.direction_type import DirectionType
from spells.spell_definition import CORNER_PAUSE, SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup


def arresto_momentum() -> SpellDefinition:
    """
    Zigzag motif: NE up-stroke → SE down-stroke, repeated 2–4 times. Each NE up-stroke is
    treated as required so the spell can't be satisfied by SE-only motion. Optional CORNER_PAUSE
    steps absorb deliberate pauses at zigzag corners; they're skipped when corners are sharp.
    """
    return SpellDefinition(
        step_groups=[
            SpellStepGroup(
                name="zigzag_pair",
                steps=[
                    SpellStep(frozenset({DirectionType.MOVING_N, DirectionType.MOVING_NE}), required=True),
                    CORNER_PAUSE,
                    SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE})),
                    CORNER_PAUSE,
                ],
                relative_distance=1.0,
                relative_duration=1.0,
                repeat_min=2,
                repeat_max=4,
            ),
        ],
        min_spell_steps=4,
        min_total_duration_s=0.8,
        max_total_duration_s=3.0,
        max_idle_gap_s=1,
        max_filler_duration_s=1,
        check_duration=True,
        check_group_distance_ratio=False,
    )
