from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from spells.spell_type import SpellType


@dataclass
class UnityUdpTxSettings(SettingsBase):
    spell_mapping_keys: list[str]
    spell_mapping_values: list[str]
    udp_tx: UdpTxSettings

    @property
    def spell_mappings(self) -> dict[str, str]:
        return {k: v for k, v in zip(self.spell_mapping_keys, self.spell_mapping_values)}
