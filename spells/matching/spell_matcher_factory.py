from logging import Logger

from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.spell_matcher import SpellMatcher


class SpellMatcherFactory:
    def __init__(self, logger: Logger, spell_accuracy_scorer: SpellAccuracyScorer) -> None:
        self._spell_accuracy_scorer = spell_accuracy_scorer
        self._logger = logger

    def create(self) -> SpellMatcher:
        return SpellMatcher(self._logger, self._spell_accuracy_scorer)
