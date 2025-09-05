# rx.py
import asyncio

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from classification.classifiers.spells.spell import Spell
from classification.classifiers.spells.spell_factory import SpellFactory
from detection.detected_gestures import DetectedGestures
from detection.gesture_history import GestureHistory
from display.images.libraries.configuration.image_library_settings import ImageLibrarySettings
from display.images.libraries.gesture_image_library import GestureImageLibrary
from display.images.libraries.spell_image_library import SpellImageLibrary
from display.spellcasting_visualiser import SpellcastingVisualiser
from gamevolt.display.configuration.image_visualiser_settings import ImageVisualiserSettings
from gamevolt.display.image_visualiser import ImageVisualiser
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.configuration.udp_peer_settings import UdpPeerSettings
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp_peer import UdpPeer
from input.spell_provider import SpellProvider
from messaging.target_gestures_message import TargetGesturesMessage
from spell_checker import SpellChecker
from spell_type import SpellType
from wand_client import WandClient


async def main() -> None:
    logger = get_logger(LoggingSettings("./Logs/wand_tracking.log", "DEBUG"))
    udp_peer = UdpPeer(
        logger,
        settings=UdpPeerSettings(
            udp_tx=UdpTxSettings(
                host="127.0.0.1",
                port=9999,
            ),
            udp_rx=UdpRxSettings(
                host="127.0.0.1",
                port=9998,
                max_size=65536,
                recv_timeout_s=0.25,
            ),
        ),
    )

    message_handler = MessageHandler(logger, udp_peer)
    wand_client = WandClient(logger, message_handler)

    def on_gestures_detected(detected_gestures: DetectedGestures) -> None:
        gesture_history.append(detected_gestures)

    def on_spell(type: SpellType) -> None:
        print(f"You cast ✨✨✨ {type.name} ✨✨✨!!!")

    def on_spell_targets_updated(spells: list[Spell]) -> None:
        gesture_names = []

        for spell in spell_provider.target_spells:
            gesture_names.extend([g.name for g in spell.get_gestures()])

        udp_peer.send(TargetGesturesMessage(GestureNames=gesture_names))

    visualiser = ImageVisualiser(settings=ImageVisualiserSettings(500, 500, "Gestures", 60))
    spell_image_library = SpellImageLibrary(settings=ImageLibrarySettings(assets_dir="./display/images/spells", image_size=300))
    small_image_library = GestureImageLibrary(settings=ImageLibrarySettings(assets_dir="./display/images/primitives", image_size=60))

    gesture_history = GestureHistory(10)
    spell_factory = SpellFactory()
    spell_provider = SpellProvider(logger=logger, spell_factory=spell_factory, root=visualiser.toolbar)
    spellcasting_visualiser = SpellcastingVisualiser(
        logger, spell_image_library, small_image_library, visualiser, gesture_history, spell_provider
    )

    spell_checker = SpellChecker(logger, spell_provider, gesture_history)

    wand_client.gesture_detected.subscribe(on_gestures_detected)
    spell_checker.spell_detected.subscribe(on_spell)
    spell_provider.target_spells_updated.subscribe(on_spell_targets_updated)

    logger.info("Starting gesture visualiser...")
    spellcasting_visualiser.start()
    message_handler.start()
    wand_client.start()
    spell_provider.start()
    spell_checker.start()

    try:
        while True:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Stopping gesture visualiser...")
        message_handler.stop()
        spellcasting_visualiser.stop()
        logger.info("Stopped gesture visualiser.")


asyncio.run(main())
