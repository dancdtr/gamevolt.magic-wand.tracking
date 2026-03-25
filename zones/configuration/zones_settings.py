from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from zones.configuration.zone_settings import ZoneSettings


@dataclass
class ZonesSettings(SettingsBase):
    udp_receiver: UdpRxSettings
    zones: list[ZoneSettings]
