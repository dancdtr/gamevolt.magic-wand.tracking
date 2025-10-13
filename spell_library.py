from __future__ import annotations

from motion.direction_type import DirectionType
from motion.motion_processor import DirectionType
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep
from spells.spell_step_group import SpellStepGroup

SQUARIO = SpellDefinition(
    id="SP100",
    name="SQUARIO",
    step_groups=[
        SpellStepGroup(
            name="Up",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=1 / 4,
        ),
        SpellStepGroup(
            name="Right",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
            ],
            relative_distance=1 / 4,
        ),
        SpellStepGroup(
            name="Down",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
            ],
            relative_distance=1 / 4,
        ),
        SpellStepGroup(
            name="Left",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_W}), required=True),
            ],
            relative_distance=1 / 4,
        ),
    ],
    min_spell_steps=4,
    max_total_duration_s=5.0,
    max_idle_gap_s=0.8,
)

RECTANGLIA = SpellDefinition(
    id="SP101",
    name="RECTANGLIA",
    step_groups=[
        SpellStepGroup(
            name="Up",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=4 / 10,
        ),
        SpellStepGroup(
            name="Right",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
            ],
            relative_distance=1.5 / 10,
        ),
        SpellStepGroup(
            name="Down",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
            ],
            relative_distance=4 / 10,
        ),
        SpellStepGroup(
            name="Left",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_W}), required=True),
            ],
            relative_distance=1.5 / 10,
        ),
    ],
    min_spell_steps=4,
    max_total_duration_s=5.0,
    max_idle_gap_s=0.8,
)

OBLONGIUM = SpellDefinition(
    id="SP102",
    name="OBLONGIUM",
    step_groups=[
        SpellStepGroup(
            name="Up",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=1.5 / 10,
        ),
        SpellStepGroup(
            name="Right",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
            ],
            relative_distance=4 / 10,
        ),
        SpellStepGroup(
            name="Down",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_S}), required=True),
            ],
            relative_distance=1.5 / 10,
        ),
        SpellStepGroup(
            name="Left",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_W}), required=True),
            ],
            relative_distance=4 / 10,
        ),
    ],
    min_spell_steps=4,
    max_total_duration_s=5.0,
    max_idle_gap_s=0.8,
)


REVELIO = SpellDefinition(
    id="SP001",
    name="REVELIO",
    step_groups=[
        SpellStepGroup(
            name="Line_N",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=3 / 9,
        ),
        SpellStepGroup(
            name="Curve_270_CW_Start_E",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_NE})),
                SpellStep(frozenset({DirectionType.MOVING_E, DirectionType.MOVING_NE, DirectionType.MOVING_SE}), 0.03, required=True),
                SpellStep(frozenset({DirectionType.MOVING_SE})),
                SpellStep(frozenset({DirectionType.MOVING_S, DirectionType.MOVING_SE, DirectionType.MOVING_SW}), 0.03, required=True),
                SpellStep(frozenset({DirectionType.MOVING_SW})),
                SpellStep(frozenset({DirectionType.MOVING_W})),
            ],
            relative_distance=4 / 9,
        ),
        SpellStepGroup(
            name="Line_SE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SE}), required=True),
            ],
            relative_distance=2 / 9,
        ),
    ],
    min_spell_steps=5,
    max_total_duration_s=5.0,
    max_idle_gap_s=1.20,
)

LOCOMOTOR = SpellDefinition(
    id="SP002",
    name="LOCOMOTOR",
    step_groups=[
        SpellStepGroup(
            name="Line_N",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_N}), required=True),
            ],
            relative_distance=1 / 3,
        ),
        SpellStepGroup(
            name="Line_SW",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SW}), required=True),
            ],
            relative_distance=1 / 3,
        ),
        SpellStepGroup(
            name="Line_E",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
            ],
            relative_distance=1 / 3,
        ),
    ],
    min_spell_steps=3,
    max_total_duration_s=5.0,
    max_idle_gap_s=1.20,
)

SWITCHING = SpellDefinition(
    id="SP020",
    name="SWITCHING",
    step_groups=[
        SpellStepGroup(
            name="Flick_SE",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_SE, DirectionType.MOVING_S}), required=True),
                SpellStep(frozenset({DirectionType.MOVING_S}), required=False),
            ],
            relative_distance=1 / 2,
        ),
        SpellStepGroup(
            name="Line_E",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
            ],
            relative_distance=1 / 2,
        ),
    ],
    min_spell_steps=2,
    max_total_duration_s=5.0,
    max_idle_gap_s=1.20,
)

RICTUMSEMPRA = SpellDefinition(
    id="SP009",
    name="RICTUMSEMPRA",
    step_groups=[
        SpellStepGroup(
            name="Wiggle_e",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
                SpellStep(frozenset({DirectionType.MOVING_NE}), required=True),
                # SpellStep(frozenset({DirectionType.MOVING_NE}), required=False),
            ],
            relative_distance=3 / 5,
        ),
        SpellStepGroup(
            name="Upper_beak",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_E}), required=True),
            ],
            relative_distance=2 / 5,
        ),
        SpellStepGroup(
            name="Lower_beak",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_W}), required=False),
                SpellStep(frozenset({DirectionType.MOVING_SW, DirectionType.MOVING_W}), required=True),
                SpellStep(frozenset({DirectionType.MOVING_W}), required=False),
            ],
            relative_distance=3 / 6,
        ),
        SpellStepGroup(
            name="Hook",
            steps=[
                SpellStep(frozenset({DirectionType.MOVING_W}), required=False),
                SpellStep(frozenset({DirectionType.MOVING_NW}), required=False),
                SpellStep(frozenset({DirectionType.MOVING_N}), required=False),
                SpellStep(frozenset({DirectionType.MOVING_NE}), required=True),
            ],
            relative_distance=3 / 6,
        ),
    ],
    min_spell_steps=2,
    max_total_duration_s=5.0,
    max_idle_gap_s=1.20,
)
