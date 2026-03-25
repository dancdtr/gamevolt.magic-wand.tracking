from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from wizards.wizard_level import WizardLevel


@dataclass
class WandSpellCueControllerSettings(SettingsBase):
    wand_levels: dict[str, WizardLevel]

    FIELD_HANDLERS = {
        "wand_levels": lambda pairs: {k: WizardLevel[v.upper()] for k, v in pairs},
    }
