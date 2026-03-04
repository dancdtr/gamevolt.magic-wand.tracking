# main2.py

from __future__ import annotations

import asyncio
import os

from gamevolt_logging import get_logger

from appsettings import AppSettings
from gamevolt.io.utils import bundled_path, install_path
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.serial.multi_line_receiver import MultiLineReceiver
from gamevolt.serial.serial_receiver import SerialReceiver
from messaging.spell_cast_udp_tx import SpellCastUdpTx
from motion.gesture.gesture_history import GestureHistory
from motion.gesture.gesture_history_factory import GestureHistoryFactory
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.control.spell_controller import SpellController
from spells.matching.spell_matcher_factory import SpellMatcherFactory
from spells.spell_list import SpellList
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from visualisation.configuration.visualised_wand_factory import VisualisedWandFactory
from visualisation.trail_factory import TrailFactory
from visualisation.wand_visualiser_factory import WandVisualiserFactory
from wand.motion_processor_factory import MotionProcessorFactory
from wand.tracked_wand_factory import TrackedWandFactory
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_server import WandServer
from wizards.wizard_names_provider import WizardNameProvider
from zones.zone_factory import ZoneFactory
from zones.zone_manager import ZoneManager

application_dir = os.path.dirname(os.path.abspath(__file__))
config_path = bundled_path("appsettings.yml")
config_env_path = install_path("appsettings.env.yml")
settings = AppSettings.load(config_file_path=config_path, config_env_file_path=config_env_path)
print(settings)

logger = get_logger(settings.logging.to_gamevolt_logging_settings())

history = GestureHistory(settings.motion.gesture_history)

spell_list = SpellList(logger)

spell_controller = SpellController(logger, settings.wands_udp, spell_list)

spell_matcher = SpellMatcher(logger=logger, accuracy_scorer=SpellAccuracyScorer(settings=settings.accuracy))

# line_receiver = SerialReceiver(logger=logger, settings=settings.input.server.serial_receiver)

line_receiver = MultiLineReceiver(
    logger=logger,
    line_receivers=[
        SerialReceiver(
            logger=logger,
            settings=receiver_settings,
        )
        for receiver_settings in settings.serial.receivers
    ],
)

server = WandServer(logger=logger, settings=settings.input.server, line_receiver=line_receiver)

zone_udp_receiver = UdpRx(logger, settings.zones.udp_receiver)
zone_factory = ZoneFactory(logger)
zone_message_handler = MessageHandler(logger, zone_udp_receiver)
zone_manager = ZoneManager(
    logger=logger,
    settings=settings.zones,
    message_handler=zone_message_handler,
    zone_factory=zone_factory,
)

motion_processor_factory = MotionProcessorFactory(logger, settings.motion.processor)
gesture_history_factory = GestureHistoryFactory(logger, settings.motion.gesture_history)
spell_matcher_factory = SpellMatcherFactory(logger, spell_accuracy_scorer=SpellAccuracyScorer(settings.accuracy))
name_provider = WizardNameProvider(settings.wizard)
tracked_wand_factory = TrackedWandFactory(
    logger=logger,
    settings=settings.input.wand,
    motion_processor_factory=motion_processor_factory,
    gesture_history_factory=gesture_history_factory,
    spell_matcher_factory=spell_matcher_factory,
)
tracked_wand_manager = TrackedWandManager(
    logger=logger,
    settings=settings.input,
    server=server,
    tracked_wand_factory=tracked_wand_factory,
    zone_manager=zone_manager,
    # spell_controller=spell_controller,
)

trail_factory = TrailFactory(logger, settings.wand_visualiser.trail)
visualised_wand_factory = VisualisedWandFactory(logger, trail_factory)
visualiser = WandVisualiserFactory(logger, settings.wand_visualiser, settings.input, visualised_wand_factory, tracked_wand_manager).create()

udp_tx = SpellCastUdpTx(logger, settings.wands_udp.udp_transmitter, visualiser)


def on_spell(match: SpellMatch):
    udp_tx.on_spell_detected(match)
    # tracked_wand_manager.on_spell_cast(match.wand_id)


quit_event = asyncio.Event()

spell_matcher.matched.subscribe(on_spell)
# input.position_updated.subscribe(on_position_updated)
visualiser.quit.subscribe(lambda: quit_event.set())
tracked_wand_manager.wand_rotation_updated.subscribe(visualiser.add_rotation)


async def main():
    logger.info(f"Running '{settings.name}'...")
    try:
        spell_controller.start()
        zone_manager.start()
        tracked_wand_manager.start()
        await server.start_async()
        visualiser.start()
    except Exception as ex:
        raise ex

    try:
        while not quit_event.is_set():
            # input.update()
            tracked_wand_manager.update()
            visualiser.update()
            await asyncio.sleep(0.01)
        return 0
    except Exception:
        logger.exception("Unhandled exception in wands_main")
        return 1
    finally:
        # stop/cleanup stuff (if needed)
        logger.info(f"Exited '{settings.name}'.")
