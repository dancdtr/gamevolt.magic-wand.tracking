from dataclasses import dataclass

from gamevolt.configuration.appsettings_base import AppSettingsBase
from gamevolt.messaging.udp.configuration.udp_peer_settings import UdpPeerSettings
from gv_logging.configuration.logging_settings import LoggingSettings
from motion.configuration.motion_settings import MotionSettings
from spells.accuracy.configuration.accuracy_scorer_settings import SpellAccuracyScorerSettings
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from wand.configuration.input_settings import InputSettings
from wizards.configuration.wizard_settings import WizardSettings


@dataclass
class AppSettings(AppSettingsBase):
    name: str
    logging: LoggingSettings
    input: InputSettings
    motion: MotionSettings
    wand_visualiser: WandVisualiserSettings
    accuracy: SpellAccuracyScorerSettings
    wands_udp: UdpPeerSettings
    spells_udp: UdpPeerSettings
    wizard: WizardSettings
