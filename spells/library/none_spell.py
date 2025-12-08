from spells.spell_definition import SpellDefinition


def none_spell() -> SpellDefinition:
    return SpellDefinition(
        step_groups=[],
        min_spell_steps=1,
    )
