# spells/matching/compile/spell_compiler.py
from __future__ import annotations

from spells.matching.compile.compiled_spell import CompiledSpell
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep


class SpellCompiler:
    """
    Turns a SpellDefinition into a CompiledSpell.
    """

    def compile(self, definition: SpellDefinition) -> CompiledSpell:
        flat: list[SpellStep] = []
        group_map: list[int] = []

        for gi, grp in enumerate(definition.step_groups):
            for st in grp.steps:
                flat.append(st)
                group_map.append(gi)

        steps_rev = tuple(reversed(flat))
        step_to_group_rev = tuple(reversed(group_map))

        scorable_total = sum(1 for st in steps_rev if not st.is_pause)
        required_total = sum(1 for st in steps_rev if st.required and not st.is_pause)
        optional_total = scorable_total - required_total

        group_names = tuple(g.name for g in definition.step_groups)
        group_count = len(group_names)

        return CompiledSpell(
            definition=definition,
            steps_rev=steps_rev,
            step_to_group_rev=step_to_group_rev,
            scorable_total=scorable_total,
            required_total=required_total,
            optional_total=optional_total,
            group_count=group_count,
            group_names=group_names,
        )
