from gamevolt.configuration.appsetting import appsetting
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from zones.configuration.zone_settings import ZoneSettings


@appsetting
class ZonesSettings:
    udp_receiver: UdpRxSettings
    zones: list[ZoneSettings]
