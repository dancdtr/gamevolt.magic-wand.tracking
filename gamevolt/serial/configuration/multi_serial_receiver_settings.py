from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings


@dataclass
class MultiSerialReceiverSettings(SettingsBase):
    receivers: list[SerialReceiverSettings]
