# main3.py

import asyncio
import os
import tkinter as tk
from time import sleep

from gamevolt_logging import get_logger

from appsettings import AppSettings
from display.image_libraries.configuration.image_library_settings import ImageLibrarySettings
from display.image_libraries.configuration.spell_image_library_settings import SpellImageLibrarySettings
from display.image_libraries.spell_image_library import SpellImageLibrary
from display.image_providers.configuration.image_provider_settings import ImageProviderSettings
from display.input.visual_spell_controller import VisualSpellController
from display.spell_casting_visualiser import SpellCastingVisualiser
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from gamevolt.messaging.udp.configuration.udp_peer_settings import UdpPeerSettings
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp.udp_tx import UdpTx
from gamevolt.visualisation.configuration.canvas_settings import CanvasSettings
from gamevolt.visualisation.configuration.preview_settings import RootSettings
from gamevolt.visualisation.configuration.visualiser_settings import VisualiserSettings
from gamevolt.visualisation.visualiser import Visualiser
from messaging.hello_message import HelloMessage
from messaging.spell_cast_message import SpellCastMessage
from messaging.target_spell_updated_message import TargetSpellUpdatedMessage
from spells.spell_list import SpellList

APP_NAME = "Spellcasting Visualiser"
APP_VERSION = "0.1.0"
logger = get_logger()

root_settings = RootSettings("SpellController", 800, 800, 100)
canvas_settings = CanvasSettings(background_colour="#222", highlight_thickness=0)
visualiser_settings = VisualiserSettings(root_settings, canvas_settings)

udp_tx_settings = UdpTxSettings("0.0.0.0", 8051)
udp_rx_settings = UdpRxSettings("0.0.0.0", 8050, 65556, 2)
udp_peer_settings = UdpPeerSettings(udp_tx_settings, udp_rx_settings)


visualiser_settings = VisualiserSettings(root=root_settings, canvas=canvas_settings)
visualiser = Visualiser(logger, visualiser_settings)

instruction_settings = ImageProviderSettings("display/image_assets/spells", 500, (255, 255, 255), (0, 0, 0))
success_settings = ImageProviderSettings("display/image_assets/spells", 500, (0, 255, 0), (0, 0, 0))
spell_image_library_settings = SpellImageLibrarySettings(instruction_settings, success_settings)

image_library_settings = ImageLibrarySettings("display/image_assets/gestures", 300)

udp_tx = UdpTx(logger, udp_tx_settings)
udp_rx = UdpRx(logger, udp_rx_settings)
message_handler = MessageHandler(logger, udp_rx)

spell_list = SpellList(logger)

spell_image_library = SpellImageLibrary(spell_image_library_settings)
spell_controller = VisualSpellController(logger, spell_list, visualiser, udp_tx, parent=None)

application_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(application_dir, "appsettings.yml")
config_env_path = os.path.join(application_dir, "appsettings.env.yml")
settings = AppSettings.load(config_file_path=config_path, config_env_file_path=config_env_path)

spellcasting_visualiser = SpellCastingVisualiser(
    logger=logger,
    spell_image_library=spell_image_library,
    visualiser=visualiser,
    spell_controller=spell_controller,
)

quit_event = asyncio.Event()


def on_spell_cast(message: Message) -> None:
    if isinstance(message, SpellCastMessage):
        spell = spell_list.get_by_name(message.SpellType)
        if spell.type is spell_controller.target_spell.type:
            # if spell.type is not SpellType.NONE:
            logger.info(f"({message.WandId}) cast {message.SpellType}! ({(message.Confidence * 100):.2f}%)")
            spellcasting_visualiser.show_spell_cast_coloured(spell.type, message.Colour)
            sleep(0.3)
            spellcasting_visualiser.show_spell_instruction(spell)


def on_hello(_: Message) -> None:
    udp_tx.send(TargetSpellUpdatedMessage(spell_controller.target_spell.name).to_dict())


spellcasting_visualiser.quit.subscribe(lambda: quit_event.set())
visualiser.quit.subscribe(lambda: quit_event.set())
message_handler.subscribe(SpellCastMessage, on_spell_cast)
message_handler.subscribe(HelloMessage, on_hello)


async def run_app() -> None:

    logger.info(f"Running '{APP_NAME}' version '{APP_VERSION}'...")

    try:
        message_handler.start()
        spell_controller.start()
        spellcasting_visualiser.start()
    except Exception as ex:
        logger.exception(f"Failed to start application: {ex}")
        return

    try:
        while not quit_event.is_set():
            visualiser.update()
            await asyncio.sleep(0.01)
    except tk.TclError:
        logger.info("Tkinter window closed.")
    except Exception as ex:
        logger.exception(f"Unhandled exception in main loop: {ex}")
    finally:
        logger.info("Shutting down...")
        try:
            spell_controller.stop()
        except Exception as ex:
            logger.warning(f"Error while stopping spell controller: {ex}")

        try:
            spellcasting_visualiser.stop()
        except Exception as ex:
            logger.warning(f"Error while stopping visualiser: {ex}")

        logger.info(f"Exited '{APP_NAME}'.")


if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        logger.info("Exiting on user interrupt...")
