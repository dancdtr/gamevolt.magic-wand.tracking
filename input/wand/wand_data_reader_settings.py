from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings


@dataclass
class WandDataReaderSettings(SettingsBase):
    serial_receiver: SerialReceiverSettings
    imu_hz: float
    target_hz: float
