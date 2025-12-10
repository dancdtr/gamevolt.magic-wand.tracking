from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings


@dataclass
class WandClientSettings(SettingsBase):
    imu_hz: float
    target_hz: float


@dataclass
class WandServerSettings(SettingsBase):
    serial_receiver: SerialReceiverSettings
    client: WandClientSettings
