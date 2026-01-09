from __future__ import annotations

import asyncio
import os
import tkinter as tk

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from appsettings import AppSettings
from messaging.spell_cast_udp_tx import SpellCastUdpTx
from motion.gesture.gesture_history import GestureHistory
from motion.gesture.gesture_history_factory import GestureHistoryFactory
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.control.udp_spell_controller import UdpSpellController
from spells.spell_list import SpellList
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from visualisation.configuration.visualised_wand_factory import VisualisedWandFactory
from visualisation.trail_factory import TrailFactory
from visualisation.wand_visualiser_factory import WandVisualiserFactory
from wand.tracked_wand_factory import MotionProcessorFactory
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_server import WandServer
from wizards.wizard_names_provider import WizardNameProvider

application_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(application_dir, "appsettings.yml")
config_env_path = os.path.join(application_dir, "appsettings.env.yml")
settings = AppSettings.load(config_file_path=config_path, config_env_file_path=config_env_path)
print(settings)

logger = get_logger(LoggingSettings(file_path=settings.logging.file_path, minimum_level=settings.logging.minimum_level))

history = GestureHistory(settings.motion.gesture_history)

spell_list = SpellList(logger)

spell_controller = UdpSpellController(logger, settings.udp_peer, spell_list)

spell_matcher = SpellMatcher(
    logger=logger, accuracy_scorer=SpellAccuracyScorer(settings=settings.accuracy), spell_controller=spell_controller
)

server = WandServer(logger, settings.input.server)

motion_processor_factory = MotionProcessorFactory(logger, settings.motion.processor)
gesture_history_factory = GestureHistoryFactory(logger, settings.motion.gesture_history)
name_provider = WizardNameProvider(settings.wizard)
tracked_wand_manager = TrackedWandManager(logger, settings.input, server, motion_processor_factory, gesture_history_factory, spell_matcher)

trail_factory = TrailFactory(logger, settings.wand_visualiser.trail)
visualised_wand_factory = VisualisedWandFactory(logger, trail_factory)
visualiser = WandVisualiserFactory(logger, settings.wand_visualiser, settings.input, visualised_wand_factory, tracked_wand_manager).create()

udp_tx = SpellCastUdpTx(logger, settings.udp_peer.udp_transmitter, visualiser)


def on_spell(match: SpellMatch):
    udp_tx.on_spell_detected(match)
    # tracked_wand_manager.on_spell_cast(match.wand_id)


quit_event = asyncio.Event()

spell_matcher.matched.subscribe(on_spell)
# input.position_updated.subscribe(on_position_updated)
visualiser.quit.subscribe(lambda: quit_event.set())
tracked_wand_manager.wand_rotation_updated.subscribe(visualiser.add_rotation)


async def main():
    logger.info(f"Running '{settings.name}' version: '{settings.version}'...")
    try:
        spell_controller.start()
        spell_matcher.start()
        tracked_wand_manager.start()
        await server.start()
        visualiser.start()
    except Exception as ex:
        raise ex

    try:
        while not quit_event.is_set():
            # input.update()
            tracked_wand_manager.update()
            visualiser.update()
            await asyncio.sleep(0.01)
    except tk.TclError:
        pass
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting on user interrupt...")
    finally:
        logger.info(f"Exited '{settings.name}'.")
