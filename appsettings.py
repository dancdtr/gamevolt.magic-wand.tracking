from dataclasses import dataclass

from analysis.spell_trace_session_settings import SpellTraceSessionSettings
from gamevolt.configuration.appsettings_base import AppSettingsBase
from gamevolt.configuration.settings_base import SettingsBase
from input.configuration.input_settings import InputSettings
from live_wand_preview import LiveWandPreviewSettings
from motion.configuration.motion_settings import MotionSettings
from preview.configuration.visualiser_settings import VisualiserSettings
from spells.configuration.spells_settings import SpellsSettings
from wizards.configuration.wizard_settings import WizardSettings


# shim for incompatible GV logging module settings
@dataclass
class LoggingSettings(SettingsBase):
    file_path: str
    minimum_level: str


@dataclass
class AppSettings(AppSettingsBase):
    name: str
    logging: LoggingSettings
    spells: SpellsSettings
    input: InputSettings
    motion: MotionSettings
    visualiser: VisualiserSettings
    live_wand_preview: LiveWandPreviewSettings
    spell_trace_session: SpellTraceSessionSettings
    wizard: WizardSettings
