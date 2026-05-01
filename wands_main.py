from __future__ import annotations

import asyncio
import os

from anchor_area.anchor_area_manager import AnchorAreaManager
from appsettings import AppSettings
from display.image_libraries.spell_image_library import SpellImageLibrary
from gamevolt.io.utils import bundled_path, install_path
from gamevolt.logging import get_logger
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp.udp_tx import UdpTx
from gamevolt.visualisation.visualiser import Visualiser
from gamevolt.web_sockets.web_socket_server import WebSocketServer
from motion.gesture.gesture_history_factory import GestureHistoryFactory
from receivers.web_socket_line_receiver import WebSocketLineReceiver
from show_system.show_system_controller import ShowSystemController
from spell_cues.wand_spell_cue_controller import WandSpellCueController
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.matching.spell_matcher_factory import SpellMatcherFactory
from spells.spell_cast_presentation_controller import SpellCastPresentationController
from spells.spell_registry import SpellRegistry
from visualisation.configuration.visualised_wand_factory import VisualisedWandFactory
from visualisation.trail_factory import TrailFactory
from visualisation.wand_colour_registry import WandColourRegistry
from visualisation.wand_visualiser_factory import WandVisualiserFactory
from wand.motion_processor_factory import MotionProcessorFactory
from wand.tracked_wand_factory import TrackedWandFactory
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_device_controller import WandDeviceController
from wand.wand_server import WandServer
from zones.zone_application_builder import ZoneApplicationBuilder
from zones.zone_factory import ZoneFactory
from zones.zone_manager import ZoneManager

application_dir = os.path.dirname(os.path.abspath(__file__))
config_path = bundled_path("appsettings.yml")
config_env_path = install_path("appsettings.env.yml")
settings = AppSettings.load(config_file_path=config_path, config_env_file_path=config_env_path)
print(settings)

logger = get_logger(settings.logging)

spell_registry = SpellRegistry(logger, settings.spell_registry)
web_socket_server = WebSocketServer(logger, settings.server.web_socket)
zone_message_handler = None


zone_factory = ZoneFactory(logger)
builder = ZoneApplicationBuilder(logger)
zone_udp_receiver: UdpRx | None = None

if settings.is_dev:
    zone_visualiser_host = Visualiser(logger, settings.zone_visualisation.visualiser)

    spell_image_library = SpellImageLibrary(settings.spell_image_library)

    zone_application = builder.build_mock(
        spell_image_library=spell_image_library,
        visualiser=zone_visualiser_host,
        spell_registry=spell_registry,
    )
else:
    zone_udp_receiver = UdpRx(logger, settings.zones.udp_receiver)
    zone_message_handler = MessageHandler(logger, zone_udp_receiver)

    production_zone_manager = ZoneManager(
        message_handler=zone_message_handler,
        web_socket_server=web_socket_server,
        zone_factory=zone_factory,
        settings=settings.zones,
        logger=logger,
    )

    zone_application = builder.build_production(zone_manager=production_zone_manager)

zone_manager = zone_application.zone_manager

line_receiver = WebSocketLineReceiver(logger=logger, web_socket_server=web_socket_server)

server = WandServer(
    logger=logger,
    settings=settings.server,
    line_receiver=line_receiver,
)

motion_processor_factory = MotionProcessorFactory(logger, settings.motion.processor)
gesture_history_factory = GestureHistoryFactory(logger, settings.motion.gesture_history)
spell_matcher_factory = SpellMatcherFactory(
    spell_accuracy_scorer=SpellAccuracyScorer(settings.accuracy),
    logger=logger,
)

tracked_wand_factory = TrackedWandFactory(
    motion_processor_factory=motion_processor_factory,
    gesture_history_factory=gesture_history_factory,
    spell_matcher_factory=spell_matcher_factory,
    settings=settings.input.wand,
    logger=logger,
)

anchor_area_manager = AnchorAreaManager(
    settings=settings.anchor_area_manager,
    web_socket_server=web_socket_server,
    zone_manager=zone_manager,
    logger=logger,
)

anchor_bridge_udp_tx = UdpTx(
    logger=logger,
    settings=settings.anchor_bridge.udp_transmitter,
)

wand_device_controller = WandDeviceController(
    settings=settings.wand_device_controller,
    anchor_area_manager=anchor_area_manager,
    logger=logger,
)

tracked_wand_manager = TrackedWandManager(
    wand_device_controller=wand_device_controller,
    tracked_wand_factory=tracked_wand_factory,
    zone_manager=zone_manager,
    settings=settings.input,
    logger=logger,
    server=server,
)

anchor_area_manager.anchor_connected_for_wand.subscribe(lambda _anchor_id, wand_id: wand_device_controller.set_wand_active(wand_id))

trail_factory = TrailFactory(logger, settings.wand_visualiser.trail)
visualised_wand_factory = VisualisedWandFactory(logger, trail_factory)

wand_colour_registry = WandColourRegistry(settings.wand_colours)


wand_visualiser = WandVisualiserFactory(
    wand_visualiser_settings=settings.wand_visualiser,
    visualised_wand_factory=visualised_wand_factory,
    tracked_wand_manager=tracked_wand_manager,
    wand_colour_registry=wand_colour_registry,
    input_settings=settings.input,
    logger=logger,
).create()


show_system_udp_tx = UdpTx(logger, settings.show_system_controller.show_system_udp_tx)
lamp_tx = UdpTx(logger, settings=settings.show_system_controller.lamp_udp_tx)
show_system_controller = ShowSystemController(
    settings=settings.show_system_controller,
    show_system_tx=show_system_udp_tx,
    lamp_tx=lamp_tx,
    logger=logger,
)

spell_cast_presentation_controller = SpellCastPresentationController(
    zone_visualiser=zone_application._presentation_controller._visualiser,
    tracked_wand_manager=tracked_wand_manager,
    colour_assigner=wand_colour_registry,
    logger=logger,
)

wand_spell_cue_controller = WandSpellCueController(
    show_system_controller=show_system_controller,
    wand_device_controller=wand_device_controller,
    tracked_wand_manager=tracked_wand_manager,
    settings=settings.wand_spell_cue_controller,
    logger=logger,
)

quit_event = asyncio.Event()

wand_visualiser.quit.subscribe(lambda: quit_event.set())
zone_application.quit.subscribe(lambda: quit_event.set())
tracked_wand_manager.wand_rotation_updated.subscribe(wand_visualiser.add_rotation)


async def main() -> int:
    logger.info(f"Running '{settings.name}'...")

    try:
        if zone_udp_receiver is not None:
            await zone_udp_receiver.start_async()

        await web_socket_server.start_async()

        await zone_application.start_async()
        await spell_cast_presentation_controller.start_async()
        tracked_wand_manager.start()
        anchor_area_manager.start()
        for pinned in settings.input.tracked_wands.pinned_zones:
            for wand_id in pinned.wand_ids:
                zone_manager.pin_wand(pinned.zone_id, wand_id)
        if zone_message_handler is not None:
            zone_message_handler.start()
        wand_spell_cue_controller.start()
        line_receiver.start()

        server.start()
        wand_visualiser.start()

        # logger.info(f"Enabling all wands...")
        # for wand in tracked_wand_manager.tracked_wands():
        #     wand_device_controller.blast_wand_active(wand.id)

    except Exception:
        logger.exception("Startup failure in wands_main")
        return 1

    try:
        while not quit_event.is_set():
            tracked_wand_manager.update()
            zone_application.update()
            wand_visualiser.update()
            await asyncio.sleep(0.01)

        return 0
    except asyncio.exceptions.CancelledError:
        pass
    except Exception:
        logger.exception("Unhandled exception in wands_main")
        return 1

    finally:
        logger.info(f"Disabling all wands...")
        for wand in tracked_wand_manager.tracked_wands():
            wand_device_controller.blast_wand_inactive(wand.id)

        logger.info(f"Stopping '{settings.name}'...")
        wand_visualiser.stop()

        if zone_udp_receiver is not None:
            await zone_udp_receiver.stop_async()

        await web_socket_server.stop_async()

        await zone_application.stop_async()
        await spell_cast_presentation_controller.stop_async()
        tracked_wand_manager.stop()
        anchor_area_manager.stop()
        if zone_message_handler is not None:
            zone_message_handler.stop()
        wand_spell_cue_controller.stop()
        line_receiver.stop()

        server.stop()
        logger.info(f"Exited '{settings.name}'.")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
