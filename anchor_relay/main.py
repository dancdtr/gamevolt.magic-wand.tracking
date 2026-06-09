import asyncio

from cdtr_rtls.anchor_area import AnchorArea
from cdtr_rtls.anchor_area_controller import AnchorAreaController
from anchor_relay.anchor_relay import AnchorRelay
from anchor_relay.appsettings import AppSettingsRelay
from anchor_relay.relay_app import RelayApp
from gamevolt.io.utils import bundled_path, install_path
from gamevolt.logging import get_logger
from gamevolt.messaging.command_bridge.anchor_command_bridge import AnchorCommandBridge
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.serial.serial_transport import SerialTransport
from gamevolt.web_sockets.web_socket_client import WebSocketClient

try:
    from anchor_relay.build_info import BUILD_TIME_UTC, GIT_SHA, VERSION
except ImportError:
    VERSION, GIT_SHA, BUILD_TIME_UTC = "dev", "unknown", ""


async def main() -> int:
    appsettings_path = bundled_path("appsettings.yml")
    env_path = install_path("appsettings.env.yml")

    settings = AppSettingsRelay.load(config_file_path=appsettings_path, config_env_file_path=env_path)

    logger = get_logger(settings.logging)
    print(settings)
    logger.info(f"Build: {settings.name} v{VERSION} ({GIT_SHA}) built {BUILD_TIME_UTC or 'locally'}")

    serial_transport = SerialTransport(logger=logger, settings=settings.serial_receiver)

    additional_headers = {"Cookie": f"GameVolt-Id={settings.id}; GameVolt-Version={settings.version}"}
    web_socket_client = WebSocketClient(
        additional_headers=additional_headers,
        settings=settings.web_socket_client,
        logger=logger,
    )

    web_socket_message_handler = MessageHandler(logger, web_socket_client)
    bridge = AnchorCommandBridge(
        message_handler=web_socket_message_handler,
        serial_transport=serial_transport,
        logger=logger,
    )

    anchor_area = AnchorArea()
    anchor_area_controller = AnchorAreaController(
        message_handler=web_socket_message_handler,
        anchor_area=anchor_area,
        anchor_id=settings.id,
        logger=logger,
    )

    anchor_relay = AnchorRelay(
        logger=logger,
        line_receiver_protocol=serial_transport,
        web_socket_client=web_socket_client,
        anchor_area=anchor_area,
        bypass_presence=settings.is_dev,
    )

    app = RelayApp(
        logger=logger,
        web_socket_client=web_socket_client,
        message_handler=web_socket_message_handler,
        bridge=bridge,
        anchor_area_controller=anchor_area_controller,
        anchor_relay=anchor_relay,
    )

    logger.info(f"Running '{settings.name}' ID: ({settings.id})...")

    try:
        await app.start_async()

        while True:
            app.update()
            await asyncio.sleep(0.01)
    except asyncio.exceptions.CancelledError:
        pass
    except KeyboardInterrupt:
        logger.info(f"KeyboardInterrupt: exiting '{settings.name}' ID: ({settings.id}).")
        return 0

    except Exception:
        logger.exception(f"Unhandled exception in {settings.name}")
        return 1

    finally:
        logger.info(f"Stopping '{settings.name}' ID: ({settings.id})...")
        await app.stop_async()
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
