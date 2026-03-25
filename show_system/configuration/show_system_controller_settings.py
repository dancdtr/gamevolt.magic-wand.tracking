from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from show_system.wizard_level import WizardLevel


@dataclass
class ShowSystemControllerSettings(SettingsBase):
    show_system_udp_tx: UdpTxSettings
    lamp_udp_tx: UdpTxSettings
