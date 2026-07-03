from __future__ import annotations

from logging import Logger

from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp.udp_tx import UdpTx
from services.local_profile_service import LocalProfileService
from services.local_spell_cast_reporter import LocalSpellCastReporter
from services.local_wand_presence_reporter import LocalWandPresenceReporter
from recording.cast_image_renderer import CastImageRenderer
from recording.session_recorder import SessionRecorder
from services.wand_session_coordinator import WandSessionCoordinator
from services.wizard_session_store import WizardSessionStore
from show_system.configuration.show_system_controller_settings import ShowSystemControllerSettings
from show_system.no_op_show_system import NoOpShowSystem
from show_system.show_system import ShowSystem
from show_system.show_system_controller import ShowControlDestination, ShowSystemController
from spells.control.wand_spell_cue_controller import WandSpellCueController
from visualisation.multi_wand_visualiser_factory import MultiWandVisualiserFactory
from visualisation.wand_visualiser_factory import WandVisualiserFactory
from gamevolt.serial.serial_transport import SerialTransport
from gamevolt.tcp.configuration.tcp_client_settings import TcpClientSettings
from gamevolt.tcp.tcp_client import TcpClient
from wand.motion_processor_factory import MotionProcessorFactory
from wand.streaming.eliko.eliko_client import ElikoClient
from wand.streaming.eliko.eliko_wand_command_sink import ElikoWandCommandSink
from wand.streaming.eliko.wand_reboot_detector import WandRebootDetector
from wand.streaming.eliko_single_anchor.eliko_single_anchor_client import ElikoSingleAnchorClient
from wand.null_wand_command_sink import NullWandCommandSink
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
from zones.active_wand_zone_manager import ActiveWandZoneManager
from zones.zone_application_builder import ZoneApplicationBuilder
from zones.zone_factory import ZoneFactory

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

        # RTLS shows every active wand on one shared canvas (colour-keyed by id, corner legend);
        # the single-anchor / mock dev path keeps the single-wand window (trail + cast snapshot +
        # spell targets & zone controls), built up-front so the mock zone app can share it as its
        # zone visualiser. Spell target images render from the layered SVG templates.
        if system_type is SystemType.ELIKO_RTLS:
            wand_visualiser = MultiWandVisualiserFactory(
                logger=logger,
                settings=settings.multi_wand_visualiser,
                tracked_wand_ids=settings.tracked_wand_ids,
            ).create()
        else:
            wand_visualiser = WandVisualiserFactory(
                logger=logger,
                wand_visualiser_settings=settings.wand_visualiser,
                spell_scoring=settings.spell_scoring,
            ).create()

        if is_mock:
            zone_application = zone_application_builder.build_mock(
                zones_settings=settings.zones,
                zone_factory=zone_factory,
                visualiser=wand_visualiser,
                wand_ids=settings.tracked_wand_ids,
            )
        else:
            zone_udp_receiver = UdpRx(logger, settings.zones.udp_receiver)
            zone_message_handler = MessageHandler(logger, zone_udp_receiver)

            production_zone_manager = ActiveWandZoneManager(
                message_handler=zone_message_handler,
                zone_factory=zone_factory,
                settings=settings.zones,
                logger=logger,
            )
            zone_application = zone_application_builder.build_production(zone_manager=production_zone_manager)

        zone_manager = zone_application.zone_manager

        # Feed zone presence to the visualiser so it can add/remove a wand's trail + legend row.
        # No-op on the single-wand / headless visualisers (default protocol methods).
        def _on_visualiser_zone_enter(wand_id: str, zone_id: str) -> None:
            zone = zone_manager.get_zone(zone_id)
            wand_visualiser.wand_entered_zone(wand_id, zone_id, [spell.name for spell in zone.spell_types])

        zone_manager.wand_entered_zone.subscribe(_on_visualiser_zone_enter)
        zone_manager.wand_exited_zone.subscribe(lambda wand_id, zone_id: wand_visualiser.wand_exited_zone(wand_id))

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
            # RTLS owns wand IMU + command state; the app stays read-only on the wand.
            command_sink = NullWandCommandSink(logger=logger)
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
                manage_imu=single_settings.manage_imu,
            )
            imu_stream = imu_stream_builder.build_eliko_single_anchor(single_anchor_client)
            command_sink = ElikoWandCommandSink(
                logger=logger,
                client=single_anchor_client,
                settings=single_settings.command_sink,
            )
            if single_settings.manage_imu:
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

        zone_spell_labels = {str(spell).upper() for zone in settings.zones.zones for spell in zone.spells}

        tracked_wand_factory = TrackedWandFactory(
            motion_processor_factory=motion_processor_factory,
            settings=settings.input.wand,
            spell_scoring=settings.spell_scoring,
            zone_spell_labels=zone_spell_labels,
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

        # Visualiser dev controls: reset-XP button wipes the shared scorer's XP state;
        # the scoring-modifier toggles enable/disable each bonus (XP / cadence / tempo / pity).
        wand_visualiser.reset_xp_requested.subscribe(tracked_wand_factory.reset_xp)
        if hasattr(wand_visualiser, "scoring_modifier_changed"):
            wand_visualiser.scoring_modifier_changed.subscribe(tracked_wand_factory.set_scoring_modifier)  # type: ignore[attr-defined]

        # Single-anchor dev viewer: arming a recording starts a clean run, so reset XP
        # when the session toggles on (no-op on record-off).
        if is_mock:
            def _reset_xp_on_record(active: bool, _name: str) -> None:
                if active:
                    tracked_wand_factory.reset_xp()

            wand_visualiser.record_session_changed.subscribe(_reset_xp_on_record)

        show_system_controller = self._build_show_system(settings.show_system_controller)

        spell_cast_reporter = LocalSpellCastReporter(
            logger=logger,
            session_store=wizard_session_store,
            show_system_controller=show_system_controller,
            wand_houses=settings.wand_houses,
        )

        wand_spell_cue_controller = WandSpellCueController(
            wand_device_controller=wand_device_controller,
            tracked_wand_manager=tracked_wand_manager,
            spell_cast_reporter=spell_cast_reporter,
            logger=logger,
        )

        session_recorder = SessionRecorder(
            logger=logger,
            settings=settings.session_recorder,
            record_session_changed=wand_visualiser.record_session_changed,
            cast_attempted=tracked_wand_manager.cast_attempted,
            wand_rotation_updated=tracked_wand_manager.wand_rotation_updated,
            min_match_accuracy=settings.wand_visualiser.snapshot.min_match_accuracy,
            total_spells=tracked_wand_factory.loaded_spell_count,
            image_renderer=self._build_cast_image_renderer(),
        )

        recognition_app = RecognitionApp(
            logger=logger,
            server=server,
            tracked_wand_manager=tracked_wand_manager,
            wand_device_controller=wand_device_controller,
            wand_visualiser=wand_visualiser,
            wand_spell_cue_controller=wand_spell_cue_controller,
            session_recorder=session_recorder,
        )

        return WandsSystem(tracking=tracking_app, recognition=recognition_app)

    def _build_cast_image_renderer(self) -> CastImageRenderer | None:
        recorder = self._settings.session_recorder
        # Image rendering reuses the Qt single-wand snapshot view, so it needs the Qt
        # visualiser. Skip on headless / disabled runs — casts + points still record.
        if not (recorder.is_enabled and recorder.save_images and self._settings.wand_visualiser.is_enabled):
            return None

        from visualisation.qt.qt_cast_image_renderer import QtCastImageRenderer

        return QtCastImageRenderer(
            settings=self._settings.wand_visualiser,
            width=recorder.image_width,
            height=recorder.image_height,
        )

    def _build_show_system(self, settings: ShowSystemControllerSettings) -> ShowSystem:
        if not settings.enabled:
            self._logger.info("Show system disabled; spell casts will not be routed.")
            return NoOpShowSystem()

        destinations = [
            ShowControlDestination(
                name=dest.name,
                tx=UdpTx(self._logger, dest.udp_tx),
                spells=set(dest.spells),
            )
            for dest in settings.destinations
        ]
        if not destinations:
            self._logger.warning("Show system enabled but no destinations configured; spell casts will not be routed.")

        return ShowSystemController(logger=self._logger, destinations=destinations)
