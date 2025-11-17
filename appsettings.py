from dataclasses import dataclass

from analysis.spell_trace_session_settings import SpellTraceSessionSettings
from gamevolt.configuration.appsettings_base import AppSettingsBase
from gamevolt.visualisation.configuration.visualiser_settings import VisualiserSettings
from gv_logging.configuration.logging_settings import LoggingSettings
from input.configuration.input_settings import InputSettings
from motion.configuration.motion_settings import MotionSettings
from spells.configuration.spells_settings import SpellsSettings
from visualisation.configuration.trail_settings import TrailSettings
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from wizards.configuration.wizard_settings import WizardSettings


@dataclass
class AppSettings(AppSettingsBase):
    name: str
    logging: LoggingSettings
    spells: SpellsSettings
    input: InputSettings
    motion: MotionSettings
    wand_visualiser: WandVisualiserSettings

    spell_trace_session: SpellTraceSessionSettings
    wizard: WizardSettings
