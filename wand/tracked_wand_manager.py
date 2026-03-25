from __future__ import annotations

from typing import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from motion.motion_phase_type import MotionPhaseType
from spells.spell_type import SpellType
from wand.configuration.input_settings import InputSettings
from wand.tracked_wand import TrackedWand
from wand.tracked_wand_factory import TrackedWandFactory
from wand.wand_client import WandClient
from wand.wand_device_controller import WandDeviceController
from wand.wand_rotation import WandRotation
from wand.wand_rotation_raw import WandRotationRaw
from wand.wand_server_protocol import WandServerProtocol
from zones.zone import Zone
from zones.zone_manager_protocol import ZoneManagerProtocol


class TrackedWandManager:
    def __init__(
        self,
        logger: Logger,
        settings: InputSettings,
        server: WandServerProtocol,
        tracked_wand_factory: TrackedWandFactory,
        zone_manager: ZoneManagerProtocol,
        wand_device_controller: WandDeviceController,
    ) -> None:
        self.wand_motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.wand_rotation_updated: Event[Callable[[WandRotation], None]] = Event()
        self.spell_cast: Event[Callable[[TrackedWand, Zone, SpellType], None]] = Event()

        self._wand_device_controller = wand_device_controller
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
        self._zone_manager.zone_exited.subscribe(self._on_zone_exited)

        for id in self._settings.ids:
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

        self._zone_manager.zone_entered.unsubscribe(self._on_zone_entered)
        self._zone_manager.zone_exited.unsubscribe(self._on_zone_exited)

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

        # zone = self._zone_manager.get_zone_containing_wand_id(client.id)
        # if zone is not None:
        #     self._logger.info(f"Wand ({client.id}) reconnected and was previously in zone {zone.id}. Setting wand active.")
        #     self._wand_device_controller.set_wand_active(client.id)

        # self._wan

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

    def _on_zone_entered(self, zone: Zone, wand_id: str) -> None:
        wand = self._get_wand(wand_id)

        wand.set_spell_targets(zone.spell_types)
        wand.start()

        self._wand_device_controller.set_wand_active(wand.id)

    def _on_zone_exited(self, zone: Zone, wand_id: str) -> None:
        wand = self._get_wand(wand_id)

        wand.stop()
        wand.clear_spell_target()

        self._wand_device_controller.set_wand_inactive(wand.id)

    def _on_spell_cast(self, wand: TrackedWand, spell_type: SpellType) -> None:
        zone = self._zone_manager.get_zone_containing_wand_id(wand.id)

        self._logger.debug(f"Wand ({wand.id}) cast '{spell_type.name}'!")
        self.spell_cast.invoke(wand, zone, spell_type)

    def _get_wand(self, id: str) -> TrackedWand:
        wand = self._tracked_wands.get(id)
        if wand is None:
            raise KeyError(f"No wand with ID: ({id})!")

        return wand
