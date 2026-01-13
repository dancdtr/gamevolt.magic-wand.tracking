import tkinter as tk
from logging import Logger
from typing import Sequence

from visualisation.configuration.trail_settings import TrailColourSettings
from visualisation.trail import Trail
from wand.tracked_wand import TrackedWand
from wand.wand_rotation import WandRotation


class VisualisedWand:
    def __init__(
        self,
        logger: Logger,
        settings: TrailColourSettings,
        tracked_wand: TrackedWand,
        trail: Trail,
        canvas: tk.Canvas,
    ) -> None:
        self._logger = logger
        self.settings = settings

        self._tracked_wand = tracked_wand
        self._canvas = canvas
        self._trail = trail

        self.line_id: int | None = None
        self.dot_ids: list[int] = []

    @property
    def id(self) -> str:
        return self._tracked_wand.id

    @property
    def colour_settings(self) -> TrailColourSettings:
        return self.settings

    def start(self) -> None:
        self._tracked_wand.rotation_updated.subscribe(self._add_rotation)
        self._tracked_wand.reset.subscribe(self.reset)

    def stop(self) -> None:
        self._tracked_wand.reset.unsubscribe(self.reset)
        self._tracked_wand.rotation_updated.unsubscribe(self._add_rotation)

    def reset(self) -> None:
        self._trail.clear()
        self.erase()

    def erase(self) -> None:
        if self.line_id is not None:
            self._canvas.delete(self.line_id)
            self.line_id = None

        for dot_id in self.dot_ids:
            self._canvas.delete(dot_id)
        self.dot_ids.clear()

    def points(self) -> Sequence[tuple[float, float]]:
        return self._trail.points()

    def dispose(self) -> None:
        self.stop()
        self.reset()

    def _add_rotation(self, sample: WandRotation) -> None:
        if sample.nx is None or sample.ny is None:
            return
        self._trail.add(sample)
