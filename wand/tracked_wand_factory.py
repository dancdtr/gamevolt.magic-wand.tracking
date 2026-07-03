from gamevolt.logging import Logger
from motion.stroke.stroke_windower import StrokeWindower
from spells.matching.dollar_one.template_library import load_default_library
from spells.scoring.scoring_modifier import ScoringModifier
from spells.scoring.spell_scorer import SpellScorer
from spells.scoring.streak_tracker import InMemoryStreakTracker
from spells.scoring.xp_provider import InMemoryXpProvider
from spells.settings.spell_scoring_settings import SpellScoringSettings
from wand.configuration.wand_settings import WandSettings
from wand.interpreters.wand_forward_gravity_interpreter import ForwardGravityInterpreter
from wand.motion_processor_factory import MotionProcessorFactory
from wand.tracked_wand import TrackedWand


class TrackedWandFactory:
    def __init__(
        self,
        logger: Logger,
        settings: WandSettings,
        motion_processor_factory: MotionProcessorFactory,
        spell_scoring: SpellScoringSettings,
        zone_spell_labels: set[str] | None = None,
    ) -> None:
        self._motion_processor_factory = motion_processor_factory

        self._wand_settings = settings
        self._logger = logger

        # One shared recognizer (templates are immutable) across all wands.
        # Restricted to zone-mapped spells so unused glyphs never load.
        self._recognizer = load_default_library(logger, zone_spell_labels)
        # Shared scorer + per-player state. Keyed by wand id (wands are owned for life).
        self._scorer = SpellScorer(spell_scoring, InMemoryXpProvider(), InMemoryStreakTracker())

    @property
    def loaded_spell_count(self) -> int:
        """Number of spell templates loaded into the shared recogniser (the castable set)."""
        return self._recognizer.template_count

    def reset_xp(self) -> None:
        """Wipe accrued XP for all wands — shared scorer state."""
        self._scorer.reset_xp()

    def set_scoring_modifier(self, modifier: ScoringModifier, enabled: bool) -> None:
        """Toggle a scoring modifier (XP / cadence / tempo / pity) — shared scorer state."""
        self._scorer.set_modifier(modifier, enabled)

    def create(self, id: str) -> TrackedWand:
        return TrackedWand(
            logger=self._logger,
            settings=self._wand_settings,
            id=id,
            motion_processor=self._motion_processor_factory.create(),
            forward_interpreter=ForwardGravityInterpreter(self._wand_settings.rmf),
            stroke_windower=StrokeWindower(),
            recognizer=self._recognizer,
            scorer=self._scorer,
        )
