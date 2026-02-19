from __future__ import annotations

from logging import Logger

from spells.matching.rules.rules_factory import RulesFactory
from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext
from spells.spell import Spell
from spells.spell_definition import SpellDefinition


class RulesValidator:
    """
    Holds a precompiled, stable list of SpellRule objects for the CURRENT spell.
    Rules are rebuilt only when the target spell changes.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._rules_factory = RulesFactory(logger)

        self._current_spell: Spell | None = None
        self._rules: tuple[SpellRule, ...] = ()

    def on_spell_updated(self, spell: Spell, spell_definition: SpellDefinition) -> None:
        if self._current_spell is not None and self._current_spell.type == spell.type:
            return

        self._current_spell = spell
        self._logger.debug(f"Creating spell rules for: '{spell.name}'...")
        self._rules = self._rules_factory.create(spell_definition)

    def validate(self, ctx: SpellMatchContext) -> bool:
        if not self._rules:
            return False

        for rule in self._rules:
            if not rule.validate(ctx):
                return False

        return True

    def clear(self) -> None:
        self._current_spell = None
        self._rules = ()
