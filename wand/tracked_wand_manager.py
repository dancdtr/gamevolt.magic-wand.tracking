# tracked_wand_manager.py
from __future__ import annotations

from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from motion.gesture.gesture_history_factory import GestureHistoryFactory
from motion.motion_phase_type import MotionPhaseType
from spells.spell_matcher import SpellMatcher
from wand.configuration.input_settings import InputSettings
from wand.tracked_wand import TrackedWand
from wand.tracked_wand_factory import MotionProcessorFactory, TrackedWandFactory
from wand.wand_rotation import WandRotation
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server import WandServer


class TrackedWandManager:
    def __init__(
        self,
        logger: Logger,
        settings: InputSettings,
        server: WandServer,
        motion_processor_factory: MotionProcessorFactory,
        gesture_history_factory: GestureHistoryFactory,
        spell_matcher: SpellMatcher,
    ) -> None:
        self._logger = logger
        self._wand_settings = settings.wand

        self._server = server

        self._tracked_wand_factory = TrackedWandFactory(
            logger, settings.wand, motion_processor_factory, gesture_history_factory, spell_matcher
        )

        self._tracked_wands: dict[str, TrackedWand] = {
            tracked_wand_settings.id: self._tracked_wand_factory.create(tracked_wand_settings)
            for tracked_wand_settings in settings.tracked_wands
            if tracked_wand_settings.is_enabled
        }

        self.wand_motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.wand_rotation_updated: Event[Callable[[WandRotation], None]] = Event()

    def start(self) -> None:
        self._server.wand_rotation_raw_updated.subscribe(self._on_wand_rotation_raw)

        for tracked_wand in self._tracked_wands.values():
            tracked_wand.rotation_updated.subscribe(self._on_wand_rotation_updated)
            tracked_wand.start()

    def stop(self) -> None:
        for tracked_wand in self._tracked_wands.values():
            tracked_wand.stop()
            tracked_wand.rotation_updated.unsubscribe(self._on_wand_rotation_updated)

        self._server.wand_rotation_raw_updated.unsubscribe(self._on_wand_rotation_raw)

    def update(self) -> None:
        for wand in self._tracked_wands.values():
            wand.update()

    def tracked_wands(self) -> list[TrackedWand]:
        return list(self._tracked_wands.values())

    def _on_wand_rotation_updated(self, rotation: WandRotation) -> None:
        self.wand_rotation_updated.invoke(rotation)

    def _on_wand_rotation_raw(self, raw: WandRotationRaw) -> None:
        wand = self._tracked_wands.get(raw.id, None)

        if wand is None:
            self._logger.warning(f"No TrackedWand with ID ({raw.id})!")
            return

        wand.on_rotation_raw_updated(raw)

    def _get_wand_by_id(self, id: str) -> TrackedWand:
        wand = self._tracked_wands.get(id)
        if wand is None:
            raise KeyError(f"No tracked wand with ID: ({id})!")

        return wand
