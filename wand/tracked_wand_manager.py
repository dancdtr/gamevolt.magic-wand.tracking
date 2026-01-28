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
from wand.wand_client import WandClient
from wand.wand_rotation import WandRotation
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server import WandServer


class TrackedWandManager:
    """
    Dynamic tracked-wand lifecycle:
      - create/start TrackedWand when WandServer raises wand_connected(client)
      - stop/remove TrackedWand when WandServer raises wand_disconnected(client)
      - route WandRotationRaw updates to the active TrackedWands
    """

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
        self._server = server
        self._settings = settings.tracked_wands

        self._tracked_wand_factory = TrackedWandFactory(
            logger,
            settings.wand,
            motion_processor_factory,
            gesture_history_factory,
            spell_matcher,
        )

        # NOTE: we no longer create these up-front; we create on server connect events.

        # Live, connected tracked wands
        self._tracked_wands: dict[str, TrackedWand] = {}

        self.wand_motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.wand_rotation_updated: Event[Callable[[WandRotation], None]] = Event()

    # ── lifecycle ────────────────────────────────────────────────────────────

    def start(self) -> None:
        # Server → manager
        self._server.wand_rotation_raw_updated.subscribe(self._on_wand_rotation_raw)
        self._server.wand_connected.subscribe(self._on_wand_connected)
        self._server.wand_disconnected.subscribe(self._on_wand_disconnected)

        # If you ever add a "get currently connected clients" API on the server,
        # you could sync-create here too. For now we rely on events only.

    def stop(self) -> None:
        # Unsubscribe first to prevent events during teardown
        self._server.wand_disconnected.unsubscribe(self._on_wand_disconnected)
        self._server.wand_connected.unsubscribe(self._on_wand_connected)
        self._server.wand_rotation_raw_updated.unsubscribe(self._on_wand_rotation_raw)

        # Stop and clear all tracked wands
        for wand in list(self._tracked_wands.values()):
            wand.stop()
            wand.rotation_updated.unsubscribe(self._on_wand_rotation_updated)

        self._tracked_wands.clear()

    def update(self) -> None:
        # Let server prune clients (which will raise disconnect events)
        self._server.update()

        # Update all currently-connected wands
        for wand in self._tracked_wands.values():
            wand.update()

    # ── public helpers ───────────────────────────────────────────────────────

    def tracked_wands(self) -> list[TrackedWand]:
        return list(self._tracked_wands.values())

    def reset_wand_forwards(self) -> None:
        for wand in self.tracked_wands():
            wand.reset_forward()
            wand.reset_data()

    # def on_spell_cast(self, wand_id: str) -> None:
    #     wand_id = wand_id.upper()
    #     wand = self._tracked_wands.get(wand_id)
    #     if wand is None:
    #         self._logger.warning(f"No active TrackedWand with ID ({wand_id})")
    #         return

    #     wand.clear_gesture_history()

    # ── server event handlers ────────────────────────────────────────────────

    def _on_wand_connected(self, client: WandClient) -> None:
        wand_id = client.id.upper()

        if wand_id in self._tracked_wands:
            # Already active (can happen if duplicate connect events arrive)
            return

        if self._settings.enable_filtering and wand_id not in self._settings.filtered_ids:
            self._logger.warning(f"({wand_id}) connected but is filtered out and ignored.")
            return

        wand = self._tracked_wand_factory.create(wand_id)
        self._tracked_wands[wand_id] = wand

        wand.rotation_updated.subscribe(self._on_wand_rotation_updated)

        wand.start()
        self._logger.info(f"TrackedWand ({wand_id}) connected.")

    def _on_wand_disconnected(self, client: WandClient) -> None:
        wand_id = client.id.upper()

        wand = self._tracked_wands.pop(wand_id, None)
        if wand is None:
            return

        wand.stop()
        wand.rotation_updated.unsubscribe(self._on_wand_rotation_updated)

        self._logger.info(f"TrackedWand ({wand_id}) disconnected.")

    # ── tracked wand → manager events ────────────────────────────────────────

    def _on_wand_rotation_updated(self, rotation: WandRotation) -> None:
        self.wand_rotation_updated.invoke(rotation)

    # ── server raw routing ───────────────────────────────────────────────────

    def _on_wand_rotation_raw(self, raw: WandRotationRaw) -> None:
        wand_id = raw.id.upper()
        wand = self._tracked_wands.get(wand_id)

        if wand is None:
            # This can occur if raw arrives before connect is handled or after disconnect.
            # Usually harmless; just ignore.
            self._logger.debug(f"Raw rotation for inactive wand ({wand_id}); ignoring.")
            return

        wand.on_rotation_raw_updated(raw)
