import argparse
import asyncio

from gamevolt_logging import get_logger

from anchor_gateway_app.anchor_gateway import AnchorGateway
from anchor_gateway_app.configuration.anchor_gateway_appsettings import AnchorGatewayAppSettings
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp.udp_to_serial_command_bridge import CommandBridgeSettings, UdpToSerialCommandBridge
from gamevolt.serial.serial_receiver import SerialReceiver
from gamevolt.serial.serial_transport import SerialTransport
from gamevolt.web_sockets.web_socket_client import WebSocketClient


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="GatewayMain",
        description="Wand data relay for connected UWB anchor.",
    )
    p.add_argument("--id", required=True, help="Gateway ID (used to select config file), e.g. 1,2,3")
    return p.parse_args()


async def run() -> int:
    args = parse_args()

    config_path = f"./anchor_gateway_{args.id}_appsettings.yml"
    settings = AnchorGatewayAppSettings.load(config_file_path=config_path, config_env_file_path=None)

    logger = get_logger(settings.logging.to_gamevolt_logging_settings())
    print(settings)

    serial_transport = SerialTransport(logger=logger, settings=settings.serial_receiver)

    udp_rx = UdpRx(
        logger=logger,
        settings=UdpRxSettings(host="127.0.0.1", port=40100, max_size=4096, recv_timeout_s=1),
    )

    bridge = UdpToSerialCommandBridge(
        logger=logger,
        udp_rx=udp_rx,
        serial_transport=serial_transport,
        settings=CommandBridgeSettings(repeat=2),
    )

    additional_headers = {"Cookie": f"GameVolt-Id={settings.id}; GameVolt-Version={settings.version}"}
    web_socket_client = WebSocketClient(
        logger=logger,
        settings=settings.web_socket_client,
        additional_headers=additional_headers,
    )

    gateway = AnchorGateway(
        logger=logger,
        line_receiver_protocol=serial_transport,
        web_socket_client=web_socket_client,
    )

    # Optional: attach to keep linters happy / keep strong reference
    gateway.command_bridge = bridge  # type: ignore[attr-defined]

    logger.info(f"Running '{settings.name}' ID: ({settings.id})...")

    try:
        # Start UDP (threaded, non-async)
        await udp_rx.start_async()

        await gateway.start_async()

        while True:
            gateway.update()
            await asyncio.sleep(0.01)

    except KeyboardInterrupt:
        logger.info(f"KeyboardInterrupt: exiting '{settings.name}' ID: ({settings.id}).")
        return 0

    except Exception:
        logger.exception(f"Unhandled exception in {settings.name}")
        return 1

    finally:
        logger.info(f"Stopping '{settings.name}' ID: ({settings.id})...")
        try:
            await udp_rx.stop_async()
        except Exception:
            logger.exception("Error while stopping UdpRx")
        try:
            await gateway.stop_async()
        except Exception:
            logger.exception(f"Error while stopping {settings.name}")


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
