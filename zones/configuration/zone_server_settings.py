from dataclasses import dataclass

from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings


@dataclass
class ZoneServerSettings:
    udp: UdpRxSettings
