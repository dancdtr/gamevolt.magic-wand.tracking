from logging import Logger

from visualisation.configuration.trail_settings import TrailSettings
from visualisation.trail import Trail


class TrailFactory:
    def __init__(self, logger: Logger, settings: TrailSettings) -> None:
        self._settings = settings
        self._logger = logger

    def create(self) -> Trail:
        return Trail(self._settings)
