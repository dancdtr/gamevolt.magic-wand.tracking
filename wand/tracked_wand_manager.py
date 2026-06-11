from __future__ import annotations

from typing import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from motion.motion_phase_type import MotionPhaseType
from spells.spell_cast import SpellCast
from wand.tracked_wand import TrackedWand
from wand.tracked_wand_factory import TrackedWandFactory
from wand.wand_client import WandClient
from wand.wand_device_controller import WandDeviceController
from wand.wand_rotation import WandRotation
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server_protocol import WandServerProtocol
from zones.zone_manager_protocol import ZoneManagerProtocol


class TrackedWandManager:
    def __init__(
        self,
        logger: Logger,
        tracked_wand_ids: list[str],
        server: WandServerProtocol,
        tracked_wand_factory: TrackedWandFactory,
        zone_manager: ZoneManagerProtocol,
        wand_device_controller: WandDeviceController,
    ) -> None:
        self.wand_motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.wand_rotation_updated: Event[Callable[[WandRotation], None]] = Event()
        self.spell_cast: Event[Callable[[SpellCast], None]] = Event()

        self._wand_device_controller = wand_device_controller
        self._tracked_wand_factory = tracked_wand_factory
        self._tracked_wand_ids = list(tracked_wand_ids)
        self._zone_manager = zone_manager
        self._server = server
        self._logger = logger

        self._tracked_wands: dict[str, TrackedWand] = {}

    def start(self) -> None:
        self._server.wand_rotation_raw_updated.subscribe(self._on_wand_rotation_raw)
        self._server.wand_disconnected.subscribe(self._on_wand_disconnected)
        self._server.wand_connected.subscribe(self._on_wand_connected)

        self._zone_manager.wand_entered_zone.subscribe(self._on_wand_entered_zone)
        self._zone_manager.wand_exited_zone.subscribe(self._on_wand_exited_zone)

        for id in self._tracked_wand_ids:
            wand = self._tracked_wand_factory.create(id)
            self._tracked_wands[id] = wand

            wand.rotation_updated.subscribe(self._on_wand_rotation_updated)
            wand.spell_cast.subscribe(self._on_spell_cast)

            self._logger.info(f"TrackedWand ({id}) created.")

    def stop(self) -> None:
        for wand in list(self._tracked_wands.values()):
            wand.stop()
            wand.rotation_updated.unsubscribe(self._on_wand_rotation_updated)

        self._tracked_wands.clear()
        self._server.wand_rotation_raw_updated.unsubscribe(self._on_wand_rotation_raw)
        self._server.wand_disconnected.unsubscribe(self._on_wand_disconnected)
        self._server.wand_connected.unsubscribe(self._on_wand_connected)

        self._zone_manager.wand_entered_zone.unsubscribe(self._on_wand_entered_zone)
        self._zone_manager.wand_exited_zone.unsubscribe(self._on_wand_exited_zone)

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

    def _on_wand_connected(self, client: WandClient) -> None:
        self._logger.debug(f"Wand ({client.id}) connected.")

        # Wand TX state lives on the wand; a disconnect (radio dropout, power
        # cycle, OTA command burst stalling PR for > disconnect_after_s) loses
        # it. Zone presence is held by ZoneManager and is unaware of wand
        # connectivity, so no fresh zone_enter fires on reconnect. Re-activate
        # here if the wand is still in a zone, and reset the forward
        # interpreter so the integration restarts from the new orientation
        # instead of jumping from the pre-disconnect sample.
        wand = self._tracked_wands.get(client.id)
        if wand is None:
            return

        wand.reset()

        zone_ids = self._zone_manager.zones_containing_wand(client.id)
        if not zone_ids:
            return

        self._logger.info(f"Wand ({client.id}) reconnected while in zones {zone_ids}. Re-activating.")
        self._wand_device_controller.activate_wand(client.id)

    def _on_wand_disconnected(self, client: WandClient) -> None:
        self._logger.debug(f"Wand ({client.id}) disconnected.")

    def _on_wand_rotation_updated(self, rotation: WandRotation) -> None:
        self.wand_rotation_updated.invoke(rotation)

    def _on_wand_rotation_raw(self, raw: WandRotationRaw) -> None:
        wand_id = raw.id.upper()
        wand = self._tracked_wands.get(wand_id)

        if wand is None:
            self._logger.verbose(f"Wand ({wand_id}) ignoring raw rotation as inactive.")
            return

        wand.on_rotation_raw_updated(raw)

    def _on_wand_entered_zone(self, wand_id: str, zone_id: str) -> None:
        wand = self._get_wand(wand_id)
        zone = self._zone_manager.get_zone(zone_id)

        wand.set_spell_targets(zone.spell_types)
        wand.start()

        self._wand_device_controller.activate_wand(wand.id)

    def _on_wand_exited_zone(self, wand_id: str, zone_id: str) -> None:
        wand = self._get_wand(wand_id)

        wand.stop()
        wand.clear_spell_target()

        self._wand_device_controller.deactivate_wand(wand.id)

    def _on_spell_cast(self, cast: SpellCast) -> None:
        self._logger.debug(f"Wand ({cast.wand_id}) cast '{cast.spell_type.name}' ({cast.quality.name})!")
        self.spell_cast.invoke(cast)

    def _get_wand(self, id: str) -> TrackedWand:
        wand = self._tracked_wands.get(id)
        if wand is None:
            raise KeyError(f"No wand with ID: ({id})!")

        return wand
