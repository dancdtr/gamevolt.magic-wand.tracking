from gamevolt.configuration.appsetting import appsetting
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings


@appsetting
class ShowSystemControllerSettings:
    show_system_udp_tx: UdpTxSettings
    lamp_udp_tx: UdpTxSettings
