from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings


@dataclass
class SpellSelectorSettings(SettingsBase):
    udp_receiver: UdpRxSettings
