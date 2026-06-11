from __future__ import annotations

from logging import Logger

from display.image_libraries.spell_image_library import SpellImageLibrary
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp.udp_tx import UdpTx
from gamevolt.visualisation.visualiser import Visualiser
from services.local_profile_service import LocalProfileService
from services.local_spell_cast_reporter import LocalSpellCastReporter
from services.local_wand_presence_reporter import LocalWandPresenceReporter
from services.wand_session_coordinator import WandSessionCoordinator
from services.wizard_session_store import WizardSessionStore
from show_system.show_system_controller import ShowSystemController
from spells.control.wand_spell_cue_controller import WandSpellCueController
from spells.spell_cast_presentation_controller import SpellCastPresentationController
from visualisation.configuration.visualised_wand_factory import VisualisedWandFactory
from visualisation.trail_factory import TrailFactory
from visualisation.wand_colour_registry import WandColourRegistry
from visualisation.wand_visualiser_factory import WandVisualiserFactory
from gamevolt.serial.serial_transport import SerialTransport
from gamevolt.tcp.configuration.tcp_client_settings import TcpClientSettings
from gamevolt.tcp.tcp_client import TcpClient
from wand.motion_processor_factory import MotionProcessorFactory
from wand.streaming.eliko.eliko_client import ElikoClient
from wand.streaming.eliko.eliko_wand_command_sink import ElikoWandCommandSink
from wand.streaming.eliko.wand_reboot_detector import WandRebootDetector
from wand.streaming.eliko_single_anchor.eliko_single_anchor_client import ElikoSingleAnchorClient
from wand.streaming.wand_imu_stream import WandImuStream
from wand.streaming.wand_imu_stream_builder import WandImuStreamBuilder
from wand.tracked_wand_factory import TrackedWandFactory
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_command_sink import WandCommandSink
from wand.wand_device_controller import WandDeviceController
from wand.wand_server import WandServer
from wands_app.appsettings import AppSettings
from wands_app.configuration.system_type import SystemType
from wands_app.recognition_app import RecognitionApp
from wands_app.system import WandsSystem
from wands_app.tracking_app import TrackingApp
from wizards.configuration.wizard_settings import WizardSettings
from wizards.wizard_names_provider import WizardNameProvider
from zones.zone_application_builder import ZoneApplicationBuilder
from zones.zone_factory import ZoneFactory
from zones.zone_manager import ZoneManager

WIZARD_NAMES = ["Merlin", "Morgana", "Gandalf", "Circe", "Nimue"]


class WandsSystemBuilder:
    def __init__(self, logger: Logger, settings: AppSettings) -> None:
        self._logger = logger
        self._settings = settings

    def build(self) -> WandsSystem:
        logger = self._logger
        settings = self._settings
        system_type = settings.system_type

        zone_factory = ZoneFactory(logger)
        zone_application_builder = ZoneApplicationBuilder(logger)

        is_mock = system_type is SystemType.ELIKO_SINGLE_ANCHOR

        zone_udp_receiver: UdpRx | None = None
        zone_message_handler: MessageHandler | None = None

        if is_mock:
            zone_visualiser_host = Visualiser(logger, settings.zone_visualisation.visualiser)
            spell_image_library = SpellImageLibrary(settings.spell_image_library)

            zone_application = zone_application_builder.build_mock(
                zones_settings=settings.zones,
                zone_factory=zone_factory,
                visualiser=zone_visualiser_host,
                spell_image_library=spell_image_library,
                wand_ids=settings.tracked_wand_ids,
            )
        else:
            zone_udp_receiver = UdpRx(logger, settings.zones.udp_receiver)
            zone_message_handler = MessageHandler(logger, zone_udp_receiver)

            production_zone_manager = ZoneManager(
                message_handler=zone_message_handler,
                zone_factory=zone_factory,
                settings=settings.zones,
                logger=logger,
            )
            zone_application = zone_application_builder.build_production(zone_manager=production_zone_manager)

        zone_manager = zone_application.zone_manager

        imu_stream_builder = WandImuStreamBuilder(logger, settings.imu_stream)

        imu_stream: WandImuStream
        command_sink: WandCommandSink
        wand_reboot_detector: WandRebootDetector | None = None

        if system_type is SystemType.ELIKO_RTLS:
            eliko_settings = settings.imu_stream.eliko
            if eliko_settings is None:
                raise ValueError("system_type=eliko_rtls requires imu_stream.eliko in appsettings.")
            tcp_client = TcpClient(
                logger=logger,
                settings=TcpClientSettings(
                    host=eliko_settings.connection.host,
                    port=eliko_settings.connection.port,
                    reconnect_delay_s=eliko_settings.connection.reconnect_delay_s,
                ),
            )
            eliko_client = ElikoClient(logger=logger, settings=eliko_settings.connection, client=tcp_client)
            imu_stream = imu_stream_builder.build_eliko(eliko_client)
            command_sink = ElikoWandCommandSink(logger=logger, client=eliko_client, settings=eliko_settings.command_sink)
        else:
            single_settings = settings.imu_stream.eliko_single_anchor
            if single_settings is None:
                raise ValueError(
                    "system_type=eliko_single_anchor requires imu_stream.eliko_single_anchor in appsettings."
                )
            serial_transport = SerialTransport(logger=logger, settings=single_settings.serial)
            single_anchor_client = ElikoSingleAnchorClient(
                logger=logger,
                transport=serial_transport,
                tracked_wand_ids=settings.tracked_wand_ids,
                subscribe_flag=single_settings.subscribe_flag,
            )
            imu_stream = imu_stream_builder.build_eliko_single_anchor(single_anchor_client)
            command_sink = ElikoWandCommandSink(
                logger=logger,
                client=single_anchor_client,
                settings=single_settings.command_sink,
            )
            wand_reboot_detector = WandRebootDetector(logger=logger, line_source=single_anchor_client)
            wand_reboot_detector.wand_rebooted.subscribe(single_anchor_client.enable_imu)

        wizard_name_provider = WizardNameProvider(WizardSettings(names=WIZARD_NAMES))
        profile_service = LocalProfileService(logger=logger, name_provider=wizard_name_provider)
        presence_reporter = LocalWandPresenceReporter(logger=logger)
        wizard_session_store = WizardSessionStore()
        wand_session_coordinator = WandSessionCoordinator(
            logger=logger,
            zone_manager=zone_manager,
            profile_service=profile_service,
            presence_reporter=presence_reporter,
            session_store=wizard_session_store,
        )

        tracking_app = TrackingApp(
            logger=logger,
            imu_stream=imu_stream,
            zone_application=zone_application,
            wand_session_coordinator=wand_session_coordinator,
            zone_udp_receiver=zone_udp_receiver,
            zone_message_handler=zone_message_handler,
            wand_reboot_detector=wand_reboot_detector,
        )

        server = WandServer(
            logger=logger,
            settings=settings.server,
            imu_stream=imu_stream,
            tracked_wand_ids=settings.tracked_wand_ids,
        )

        motion_processor_factory = MotionProcessorFactory(logger, settings.motion.processor)

        tracked_wand_factory = TrackedWandFactory(
            motion_processor_factory=motion_processor_factory,
            settings=settings.input.wand,
            spell_scoring=settings.spell_scoring,
            logger=logger,
        )

        wand_device_controller = WandDeviceController(
            settings=settings.wand_device_controller,
            command_sink=command_sink,
            logger=logger,
        )

        tracked_wand_manager = TrackedWandManager(
            wand_device_controller=wand_device_controller,
            tracked_wand_factory=tracked_wand_factory,
            zone_manager=zone_manager,
            tracked_wand_ids=settings.tracked_wand_ids,
            logger=logger,
            server=server,
        )

        trail_factory = TrailFactory(logger, settings.wand_visualiser.trail)
        visualised_wand_factory = VisualisedWandFactory(logger, trail_factory)
        wand_colour_registry = WandColourRegistry(settings.wand_colours)

        wand_visualiser = WandVisualiserFactory(
            wand_visualiser_settings=settings.wand_visualiser,
            visualised_wand_factory=visualised_wand_factory,
            tracked_wand_manager=tracked_wand_manager,
            wand_colour_registry=wand_colour_registry,
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

        zone_visualiser = zone_application.zone_visualiser
        spell_cast_presentation_controller = (
            SpellCastPresentationController(
                zone_visualiser=zone_visualiser,
                tracked_wand_manager=tracked_wand_manager,
                colour_assigner=wand_colour_registry,
                logger=logger,
            )
            if zone_visualiser is not None
            else None
        )

        spell_cast_reporter = LocalSpellCastReporter(
            logger=logger,
            session_store=wizard_session_store,
            show_system_controller=show_system_controller,
        )

        wand_spell_cue_controller = WandSpellCueController(
            wand_device_controller=wand_device_controller,
            tracked_wand_manager=tracked_wand_manager,
            spell_cast_reporter=spell_cast_reporter,
            logger=logger,
        )

        recognition_app = RecognitionApp(
            logger=logger,
            server=server,
            tracked_wand_manager=tracked_wand_manager,
            wand_device_controller=wand_device_controller,
            wand_visualiser=wand_visualiser,
            wand_spell_cue_controller=wand_spell_cue_controller,
            spell_cast_presentation_controller=spell_cast_presentation_controller,
        )

        return WandsSystem(tracking=tracking_app, recognition=recognition_app)
