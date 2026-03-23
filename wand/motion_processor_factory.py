from logging import Logger

from motion.configuration.motion_processor_settings import MotionProcessorSettings
from motion.motion_processor import MotionProcessor


class MotionProcessorFactory:
    def __init__(self, logger: Logger, settings: MotionProcessorSettings) -> None:
        self._logger = logger
        self._settings = settings

    def create(self) -> MotionProcessor:
        return MotionProcessor(self._settings)
