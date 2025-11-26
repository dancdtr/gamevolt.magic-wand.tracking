from logging import Logger

from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.serial.serial_receiver import SerialReceiver
from input.motion_input_factory import MotionInputFactory
from input.wand.interpreters.configuration.rmf_settings import RMFSettings
from input.wand.interpreters.wand_yawpitch_rmf_interpreter import YawPitchRMFInterpreter
from input.wand.wand_input import WandInput
from wand_data_reader import WandDataReader

serial_settings = SerialReceiverSettings(
    port="/dev/tty.usbmodem1101",
    baud=115200,
    timeout=3,
    retry_interval=2,
)


class WandInputFactory(MotionInputFactory):
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

        self._yaw_pitch_interpreter = YawPitchRMFInterpreter(RMFSettings(invert_x=True, invert_y=True, gain_x=1.0, gain_y=1.0))
        self._wand_data_reader = WandDataReader(
            logger=logger,
            serial_reader=SerialReceiver(
                logger=logger,
                settings=serial_settings,
            ),
            imu_hz=120.0,
            target_hz=30.0,
        )

    def create(self) -> WandInput:
        return WandInput(self._logger, self._wand_data_reader, self._yaw_pitch_interpreter)
