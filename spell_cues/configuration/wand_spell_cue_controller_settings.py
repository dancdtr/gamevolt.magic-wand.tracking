from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from wizards.wizard_level_type import WizardLevelType


@dataclass
class WandSpellCueControllerSettings(SettingsBase):
    wand_levels: dict[str, WizardLevelType]

    FIELD_HANDLERS = {
        "wand_levels": lambda pairs: {k: WizardLevelType[v.upper()] for k, v in pairs},
    }
