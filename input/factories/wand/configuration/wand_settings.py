from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from input.wand.interpreters.configuration.rmf_settings import RMFSettings


@dataclass
class WandSettings(SettingsBase):
    serial_receiver: SerialReceiverSettings
    rmf: RMFSettings
    imu_hz = 120.0
    target_hz = 30.0
