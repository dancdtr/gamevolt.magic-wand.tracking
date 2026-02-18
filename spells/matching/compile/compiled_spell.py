# spells/matching/compiler/compiled_spell.py
from dataclasses import dataclass

from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep


@dataclass(frozen=True, slots=True)
class CompiledSpell:
    """
    Precomputed, immutable view of a SpellDefinition for fast matching.

    Notes:
      - steps_rev / step_to_group_rev are aligned (same length, same indices).
      - "scorable" excludes PAUSE steps (so min_spell_steps can't be satisfied by pauses).
    """

    definition: SpellDefinition

    # Reversed because matcher walks newest -> oldest through segments
    steps_rev: tuple[SpellStep, ...]
    step_to_group_rev: tuple[int, ...]

    # Totals excluding PAUSE steps
    scorable_total: int
    required_total: int
    optional_total: int

    group_count: int
    group_names: tuple[str, ...]
