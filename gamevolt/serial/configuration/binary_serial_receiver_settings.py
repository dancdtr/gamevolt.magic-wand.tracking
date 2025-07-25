from dataclasses import dataclass

from gamevolt.serial.configuration.binary_settings import BinarySettings
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings


@dataclass
class BinarySerialReceiverSettings:
    serial: SerialReceiverSettings
    binary: BinarySettings
