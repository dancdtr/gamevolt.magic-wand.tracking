from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from input.wand.interpreters.configuration.rmf_settings import RMFSettings
from input.wand.wand_data_reader_settings import WandDataReaderSettings


@dataclass
class WandSettings(SettingsBase):
    wand_data_reader: WandDataReaderSettings
    rmf: RMFSettings
