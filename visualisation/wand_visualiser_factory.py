from logging import Logger

from visualisation.configuration.visualised_wand_factory import VisualisedWandFactory
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.headless_visualiser import HeadlessVisualiser
from visualisation.visualiser_protocol import WandVisualiserProtocol
from visualisation.wand_visualiser import WandVisualiser
from wand.configuration.input_settings import InputSettings
from wand.tracked_wand_manager import TrackedWandManager


class WandVisualiserFactory:
    def __init__(
        self,
        logger: Logger,
        wand_visualiser_settings: WandVisualiserSettings,
        input_settings: InputSettings,
        visualised_wand_factory: VisualisedWandFactory,
        tracked_wand_manager: TrackedWandManager,
    ) -> None:
        self._wand_visualiser_settings = wand_visualiser_settings
        self._input_settings = input_settings
        self._visualised_wand_factory = visualised_wand_factory
        self._tracked_wand_manager = tracked_wand_manager
        self._logger = logger

    def create(self) -> WandVisualiserProtocol:
        if self._wand_visualiser_settings.is_enabled:
            return WandVisualiser(
                logger=self._logger,
                wand_visualiser_settings=self._wand_visualiser_settings,
                input_settings=self._input_settings,
                visualised_wand_factory=self._visualised_wand_factory,
                tracked_wand_manager=self._tracked_wand_manager,
            )
        else:
            return HeadlessVisualiser()
