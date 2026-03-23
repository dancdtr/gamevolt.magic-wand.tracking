from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings


@dataclass
class AnchorBridgeSettings(SettingsBase):
    udp_transmitter: UdpTxSettings
