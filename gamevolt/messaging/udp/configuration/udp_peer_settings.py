from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings


@dataclass
class UdpPeerSettings(SettingsBase):
    udp_transmitter: UdpTxSettings
    udp_receiver: UdpRxSettings
    # local_host: str
    # local_port: int
    # remote_host: str
    # remote_port: int
    # max_size: int
    # recv_timeout_s: float

    # @property
    # def get_udp_rx_settings(self) -> UdpRxSettings:
    #     return UdpRxSettings(self.local_host, self.local_port, self.max_size, self.recv_timeout_s)

    # @property
    # def get_udp_tx_settings(self) -> UdpTxSettings:
    #     return UdpTxSettings(self.remote_host, self.remote_port)
