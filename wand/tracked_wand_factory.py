from logging import Logger

from motion.gesture.gesture_history_factory import GestureHistoryFactory
from spells.matching.spell_matcher_factory import SpellMatcherFactory
from wand.configuration.wand_settings import WandSettings
from wand.motion_processor_factory import MotionProcessorFactory
from wand.tracked_wand import TrackedWand


class TrackedWandFactory:
    def __init__(
        self,
        logger: Logger,
        settings: WandSettings,
        motion_processor_factory: MotionProcessorFactory,
        gesture_history_factory: GestureHistoryFactory,
        spell_matcher_factory: SpellMatcherFactory,
    ) -> None:
        self._motion_processor_factory = motion_processor_factory
        self._gesture_history_factory = gesture_history_factory
        self._spell_matcher_factory = spell_matcher_factory

        self._wand_settings = settings
        self._logger = logger

    def create(self, id: str) -> TrackedWand:
        return TrackedWand(
            logger=self._logger,
            settings=self._wand_settings,
            id=id,
            motion_processor=self._motion_processor_factory.create(),
            gesture_history=self._gesture_history_factory.create(),
            spell_matcher=self._spell_matcher_factory.create(),
        )
