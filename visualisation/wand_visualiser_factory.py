from logging import Logger

from gamevolt.visualisation.visualiser_protocol import VisualiserProtocol
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.headless_visualiser import HeadlessVisualiser
from visualisation.wand_visualiser import WandVisualiser


class WandVisualiserFactory:
    def __init__(self, logger: Logger, settings: WandVisualiserSettings) -> None:
        self._settings = settings
        self._logger = logger

    def create(self) -> VisualiserProtocol:
        if self._settings.is_enabled:
            return WandVisualiser(self._settings)
        else:
            return HeadlessVisualiser()
