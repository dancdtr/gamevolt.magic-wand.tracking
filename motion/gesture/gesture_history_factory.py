# gesture_history_factory.py
from __future__ import annotations

from logging import Logger

from motion.gesture.configuration.gesture_history_settings import GestureHistorySettings
from motion.gesture.gesture_history import GestureHistory


class GestureHistoryFactory:
    def __init__(self, logger: Logger, settings: GestureHistorySettings):
        self._logger = logger
        self._settings = settings

    def create(self) -> GestureHistory:
        return GestureHistory(self._settings)
