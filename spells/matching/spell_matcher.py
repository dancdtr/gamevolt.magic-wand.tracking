# spells/spell_matcher.py
from __future__ import annotations

from collections.abc import Callable, Sequence
from logging import Logger

from gamevolt.events.event import Event
from motion.gesture.gesture_segment import GestureSegment
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.control.spell_controller import SpellController
from spells.library.spell_definition_factory import SpellDefinitionFactory
from spells.matching.compile.compiled_spell import CompiledSpell
from spells.matching.compile.spell_compiler import SpellCompiler
from spells.matching.engine.spell_window_matcher import SpellWindowMatcher
from spells.matching.policies.filler_policy import FillerPolicy
from spells.matching.preprocess.segment_compressor import SegmentCompressor
from spells.matching.rules.rules_validator import RulesValidator
from spells.spell import Spell
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch


class SpellMatcher:
    """
    Thin orchestrator:
      - subscribes to target spell changes
      - compresses recent segments
      - delegates matching to SpellWindowMatcher
      - emits SpellMatch via `matched` event
    """

    def __init__(
        self,
        logger: Logger,
        accuracy_scorer: SpellAccuracyScorer,
        spell_controller: SpellController,
    ) -> None:
        self._logger = logger

        self.matched: Event[Callable[[SpellMatch], None]] = Event()

        self._accuracy_scorer = accuracy_scorer
        self._rules_validator = RulesValidator()

        self._spell_controller = spell_controller
        self._spell_definition_factory = SpellDefinitionFactory()

        self._compressor = SegmentCompressor()
        self._compiler = SpellCompiler()

        self._window_matcher = SpellWindowMatcher(
            logger=self._logger,
            accuracy_scorer=self._accuracy_scorer,
            rules_validator=self._rules_validator,
            filler_policy=FillerPolicy(),
        )

        self._spell_definitions: list[SpellDefinition] = []
        self._compiled_spells: list[CompiledSpell] = []

    def start(self) -> None:
        self._spell_controller.target_spell_updated.subscribe(self._on_target_spell_updated)

    def stop(self) -> None:
        self._spell_controller.target_spell_updated.unsubscribe(self._on_target_spell_updated)

    # ----- public entry point -----
    def try_match(self, wand_id: str, history: Sequence[GestureSegment]) -> bool:
        if not history or not self._compiled_spells:
            return False

        # oldest → newest
        compressed = self._compressor.compress(history)

        for compiled in self._compiled_spells:
            match = self._window_matcher.match(
                wand_id=wand_id,
                spell_id=self._spell_controller.target_spell.code,
                spell_name=self._spell_controller.target_spell.name,
                compiled=compiled,
                segments=compressed,
            )
            if match is None:
                continue

            self._logger.info(f"({wand_id}) cast {match.spell_name}! ✨✨{match.accuracy_score * 100:.1f}% ({match.duration_s:.3f})")
            self.matched.invoke(match)
            return True

        return False

    # ----- internals -----
    def _on_target_spell_updated(self, spell: Spell) -> None:
        self._spell_definitions = [self._spell_definition_factory.create_spell(spell.type)]
        self._compiled_spells = [self._compiler.compile(d) for d in self._spell_definitions]
