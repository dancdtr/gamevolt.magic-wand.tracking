from dataclasses import dataclass

from analysis.spell_trace_session_settings import SpellTraceSessionSettings
from gamevolt.configuration.appsettings_base import AppSettingsBase
from gv_logging.configuration.logging_settings import LoggingSettings
from input.configuration.input_settings import InputSettings
from messaging.configuration.unity_udp_tx_settings import UnityUdpTxSettings
from motion.configuration.motion_settings import MotionSettings
from spells.accuracy.configuration.accuracy_scorer_settings import SpellAccuracyScorerSettings
from spells.configuration.spells_settings import SpellsSettings
from spells.selection.configuration.spell_selector_settings import SpellSelectorSettings
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from wizards.configuration.wizard_settings import WizardSettings


@dataclass
class AppSettings(AppSettingsBase):
    name: str
    version: str
    logging: LoggingSettings
    spells: SpellsSettings
    input: InputSettings
    motion: MotionSettings
    wand_visualiser: WandVisualiserSettings
    accuracy: SpellAccuracyScorerSettings
    unity_udp: UnityUdpTxSettings
    spell_selector: SpellSelectorSettings

    spell_trace_session: SpellTraceSessionSettings
    wizard: WizardSettings
