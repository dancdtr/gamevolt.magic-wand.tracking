import argparse
import asyncio

from anchor_area.anchor_area import AnchorArea
from anchor_area.anchor_area_controller import AnchorAreaController
from anchor_relay.anchor_relay import AnchorRelay
from appsettings_relay import AppSettingsRelay
from gamevolt.logging import get_logger
from gamevolt.messaging.command_bridge.anchor_command_bridge import AnchorCommandBridge
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.serial.serial_transport import SerialTransport
from gamevolt.web_sockets.web_socket_client import WebSocketClient

gateway_id: int | None = None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="RelayMain",
        description="Wand data relay for connected UWB anchor.",
    )
    p.add_argument("--id", required=False, help="Relay ID (used to select env file), e.g. 1,2,3")
    return p.parse_args()


async def main() -> int:
    args = parse_args()
    gateway_id = args.id

    appsettings_path = f"appsettings_relay.yml"

    if gateway_id:
        env_path = f"./appsettings_relay_{gateway_id}.env.yml"
    else:
        env_path = f"./appsettings_relay.env.yml"

    settings = AppSettingsRelay.load(config_file_path=appsettings_path, config_env_file_path=env_path)

    logger = get_logger(settings.logging)
    print(settings)

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

    gateway = AnchorRelay(
        logger=logger,
        line_receiver_protocol=serial_transport,
        web_socket_client=web_socket_client,
        anchor_area=anchor_area,
    )

    logger.info(f"Running '{settings.name}' ID: ({settings.id})...")

    try:
        bridge.start()
        web_socket_message_handler.start()
        await web_socket_client.start_async()
        await gateway.start_async()
        anchor_area_controller.start()

        while True:
            gateway.update()
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
        anchor_area_controller.stop()
        await gateway.stop_async()
        await web_socket_client.stop_async()
        web_socket_message_handler.stop()
        bridge.stop()
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
