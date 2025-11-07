import asyncio

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.serial.serial_receiver import SerialReceiver
from input.wand_input import WandInput
from wand_data_reader import WandDataMessage, WandDataReader
from wand_yawpitch_rmf_interpreter import RMFSettings, YawPitchRMFInterpreter

logger = get_logger(LoggingSettings(minimum_level="INFORMATION"))

serial_reader = SerialReceiver(
    logger,
    settings=SerialReceiverSettings(
        port="/dev/tty.usbmodem1101",
        baud=115200,
        timeout=3,
        retry_interval=2,
    ),
)

reader = WandDataReader(logger, serial_reader, imu_hz=120.0, target_hz=30.0)
interpreter = YawPitchRMFInterpreter(RMFSettings(invert_x=True, invert_y=True, gain_x=1.0, gain_y=1.0))

input = WandInput(logger, reader, interpreter)


# Lock the RMF frame on the very first sample
def on_first(m: WandDataMessage) -> None:
    interpreter.lock_frame_from_yawpitch(m.yaw, m.pitch)
    # If you want to zero the absolute cursor when locking:
    # interp.zero_absolute()
    reader.wand_position_updated.unsubscribe(on_first)
    logger.info(f"RMF frame locked at yaw={m.yaw:.2f}°, pitch={m.pitch:.2f}°")


reader.wand_position_updated.subscribe(on_first)
input.position_updated.subscribe(lambda x: print(x))


async def main() -> None:
    await serial_reader.start()
    input.start()

    try:
        while True:
            await asyncio.sleep(0.05)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        reader.stop()
        await serial_reader.stop()


if __name__ == "__main__":
    asyncio.run(main())
