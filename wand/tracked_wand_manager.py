from __future__ import annotations

from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from motion.motion_phase_type import MotionPhaseType
from wand.configuration.input_settings import InputSettings
from wand.tracked_wand import TrackedWand
from wand.tracked_wand_factory import TrackedWandFactory
from wand.wand_client import WandClient
from wand.wand_rotation import WandRotation
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server_protocol import WandServerProtocol
from zones.zone_manager import ZoneManager


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
        server: WandServerProtocol,
        tracked_wand_factory: TrackedWandFactory,
        zone_manager: ZoneManager,
    ) -> None:
        self.wand_motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.wand_rotation_updated: Event[Callable[[WandRotation], None]] = Event()

        self._tracked_wand_factory = tracked_wand_factory
        self._settings = settings.tracked_wands
        self._zone_manager = zone_manager
        self._server = server
        self._logger = logger

        self._tracked_wands: dict[str, TrackedWand] = {}

    def start(self) -> None:
        self._server.wand_rotation_raw_updated.subscribe(self._on_wand_rotation_raw)
        self._server.wand_disconnected.subscribe(self._on_wand_disconnected)
        self._server.wand_connected.subscribe(self._on_wand_connected)

        self._zone_manager.zone_entered.subscribe(self._on_zone_entered)

    def stop(self) -> None:
        self._server.wand_rotation_raw_updated.unsubscribe(self._on_wand_rotation_raw)
        self._server.wand_disconnected.unsubscribe(self._on_wand_disconnected)
        self._server.wand_connected.unsubscribe(self._on_wand_connected)

        for wand in list(self._tracked_wands.values()):
            wand.stop()
            wand.rotation_updated.unsubscribe(self._on_wand_rotation_updated)

        self._tracked_wands.clear()

    def update(self) -> None:
        self._server.update()

        for wand in self._tracked_wands.values():
            wand.update()

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

        self._zone_manager.on_wand_disconnected(wand.id)

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

    def _on_zone_entered(self, zone_id: str, wand_id: str) -> None:
        wand = self._get_wand(wand_id)
        zone = self._zone_manager.get_zone(zone_id)

        wand.set_spell_target(zone.spell_type)

        # wand.set_active()

    def _on_zone_exited(self, zone_id: str, wand_id: str) -> None:
        wand = self._get_wand(wand_id)
        wand.clear_spell_target()

        # if not self._zone_manager.is_wand_in_zone(wand_id):
        # wand.set_inactive()

    def _get_wand(self, id: str) -> TrackedWand:
        for k, v in self._tracked_wands.items():
            print(k, v.id)
        wand = self._tracked_wands.get(id)
        if wand is None:
            raise KeyError(f"No wand with ID: {id}!")

        return wand
