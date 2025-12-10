import tkinter as tk
from logging import Logger

from visualisation.configuration.trail_settings import TrailColourSettings
from visualisation.trail_factory import TrailFactory
from visualisation.visualised_wand import VisualisedWand
from wand.tracked_wand import TrackedWand


class VisualisedWandFactory:
    def __init__(self, logger: Logger, trail_factory: TrailFactory) -> None:
        self._trail_factory = trail_factory
        self._logger = logger

    def create(self, settings: TrailColourSettings, tracked_wand: TrackedWand, canvas: tk.Canvas) -> VisualisedWand:
        return VisualisedWand(
            logger=self._logger,
            settings=settings,
            tracked_wand=tracked_wand,
            trail=self._trail_factory.create(),
            canvas=canvas,
        )
