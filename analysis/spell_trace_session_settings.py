from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class SpellTraceSessionSettings(SettingsBase):
    natural_break_s: float  # = 0.9  # idle NONE ≥ this ends the attempt
    clear_history_on_flush: bool  # = True
    label_prefix: str  # = "TRACE"
