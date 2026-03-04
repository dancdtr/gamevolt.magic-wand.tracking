import asyncio

from gamevolt_logging import get_logger

from anchor_gateway_app.anchor_gateway import AnchorGateway
from anchor_gateway_app.configuration.anchor_gateway_appsettings import AnchorGatewayAppSettings
from gamevolt.serial.serial_receiver import SerialReceiver
from gamevolt.web_sockets.web_socket_client import WebSocketClient

config_path = "./anchor_gateway_appsettings.yml"
settings = AnchorGatewayAppSettings.load(config_file_path=config_path, config_env_file_path=None)


logger = get_logger(settings.logging.to_gamevolt_logging_settings())

print(settings)

serial_receiver = SerialReceiver(logger=logger, settings=settings.serial_receiver)
web_socket_client = WebSocketClient(logger=logger, settings=settings.web_socket_client)
gateway = AnchorGateway(logger=logger, serial_receiver=serial_receiver, websocket_client=web_socket_client)
quit_event = asyncio.Event()


async def main():
    logger.info(f"Running '{settings.name}'...")
    try:
        await gateway.start_async()
    except Exception as ex:
        raise ex

    try:
        while not quit_event.is_set():
            gateway.update()
            await asyncio.sleep(0.01)
        return 0
    except Exception:
        logger.exception(f"Unhandled exception in {settings.name}")
        return 1
    finally:
        logger.info(f"Exited '{settings.name}'.")


asyncio.run(main())
