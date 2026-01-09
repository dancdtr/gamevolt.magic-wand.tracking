from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings


@dataclass
class WandClientSettings(SettingsBase):
    imu_hz: float
    target_hz: float


@dataclass
class WandServerSettings(SettingsBase):
    header_ttl_s: float
    disconnect_after_s: float  # triggers client disconnection event if no data received for this interval
    serial_receiver: SerialReceiverSettings
    client: WandClientSettings
    filter_wands: bool
    filtered_wand_ids: list[str]
