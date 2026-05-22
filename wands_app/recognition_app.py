from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from spells.control.wand_spell_cue_controller import WandSpellCueController
from spells.spell_cast_presentation_controller import SpellCastPresentationController
from visualisation.visualiser_protocol import WandVisualiserProtocol
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_device_controller import WandDeviceController
from wand.wand_server import WandServer


class RecognitionApp:
    """Owns gesture recognition, spell matching, cue/report dispatch and
    wand visualisation. Consumes the sensor stream (via WandServer) and
    presence events produced by the TrackingApp."""

    def __init__(
        self,
        logger: Logger,
        server: WandServer,
        tracked_wand_manager: TrackedWandManager,
        wand_device_controller: WandDeviceController,
        wand_visualiser: WandVisualiserProtocol,
        wand_spell_cue_controller: WandSpellCueController,
        spell_cast_presentation_controller: SpellCastPresentationController,
    ) -> None:
        self.quit: Event[Callable[[], None]] = Event()

        self._logger = logger
        self._server = server
        self._tracked_wand_manager = tracked_wand_manager
        self._wand_device_controller = wand_device_controller
        self._wand_visualiser = wand_visualiser
        self._wand_spell_cue_controller = wand_spell_cue_controller
        self._spell_cast_presentation_controller = spell_cast_presentation_controller

        self._tracked_wand_manager.wand_rotation_updated.subscribe(self._wand_visualiser.add_rotation)
        self._wand_visualiser.quit.subscribe(self._on_quit)

    async def start_async(self) -> None:
        await self._spell_cast_presentation_controller.start_async()
        self._tracked_wand_manager.start()
        self._wand_spell_cue_controller.start()
        self._server.start()
        self._wand_visualiser.start()

    async def stop_async(self) -> None:
        self._logger.info("Disabling all wands...")
        for wand in self._tracked_wand_manager.tracked_wands():
            self._wand_device_controller.blast_wand_inactive(wand.id)

        self._wand_visualiser.stop()
        self._server.stop()
        self._wand_spell_cue_controller.stop()
        self._tracked_wand_manager.stop()
        await self._spell_cast_presentation_controller.stop_async()

        self._wand_visualiser.quit.unsubscribe(self._on_quit)
        self._tracked_wand_manager.wand_rotation_updated.unsubscribe(self._wand_visualiser.add_rotation)

    def update(self) -> None:
        self._tracked_wand_manager.update()
        self._wand_visualiser.update()

    def _on_quit(self) -> None:
        self._logger.info("RecognitionApp quit requested")
        self.quit.invoke()
