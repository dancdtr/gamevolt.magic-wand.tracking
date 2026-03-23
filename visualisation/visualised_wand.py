import tkinter as tk
from logging import Logger
from typing import Sequence

from spells.spell_type import SpellType
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
        self._tracked_wand = tracked_wand
        self._settings = settings
        self._logger = logger
        self._canvas = canvas
        self._trail = trail

        self.line_id: int | None = None
        self.dot_ids: list[int] = []

        self._x = 0.0
        self._y = 0.0

    @property
    def id(self) -> str:
        return self._tracked_wand.id

    @property
    def colour_settings(self) -> TrailColourSettings:
        return self._settings

    def start(self) -> None:
        self._tracked_wand.forward_reset.subscribe(self._on_tracked_wand_forward_reset)
        self._tracked_wand.rotation_updated.subscribe(self._add_rotation)

    def stop(self) -> None:
        self._tracked_wand.forward_reset.unsubscribe(self._on_tracked_wand_forward_reset)
        self._tracked_wand.rotation_updated.unsubscribe(self._add_rotation)

    def reset(self) -> None:
        self._x = 0.0
        self._y = 0.0
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
        if self._tracked_wand._current_spell_target is SpellType.NONE:
            return

        self._x += sample.x_delta
        self._y += sample.y_delta
        self._trail.add_xy(self._x, self._y)

    def _on_tracked_wand_forward_reset(self) -> None:
        self.reset()
