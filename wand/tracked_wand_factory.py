from logging import Logger

from motion.configuration.motion_processor_settings import MotionProcessorSettings
from motion.gesture.gesture_history_factory import GestureHistoryFactory
from motion.motion_processor import MotionProcessor
from spells.spell_matcher import SpellMatcher
from wand.configuration.tracked_wand_settings import TrackedWandSettings
from wand.configuration.wand_settings import WandSettings
from wand.tracked_wand import TrackedWand


class MotionProcessorFactory:
    def __init__(self, logger: Logger, settings: MotionProcessorSettings) -> None:
        self._logger = logger
        self._settings = settings

    def create(self) -> MotionProcessor:
        return MotionProcessor(self._settings)


class TrackedWandFactory:
    def __init__(
        self,
        logger: Logger,
        settings: WandSettings,
        motion_processor_factory: MotionProcessorFactory,
        gesture_history_factory: GestureHistoryFactory,
        spell_matcher: SpellMatcher,
    ) -> None:
        self._logger = logger
        self._wand_settings = settings

        self._motion_processor_factory = motion_processor_factory
        self._gesture_history_factory = gesture_history_factory
        self._spell_matcher = spell_matcher

    def create(self, settings: TrackedWandSettings) -> TrackedWand:
        return TrackedWand(
            logger=self._logger,
            settings=self._wand_settings,
            id=settings.id,
            motion_processor=self._motion_processor_factory.create(),
            gesture_history=self._gesture_history_factory.create(),
            spell_matcher=self._spell_matcher,
        )
