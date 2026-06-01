from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class ElikoCommandSinkSettings(SettingsBase):
    """Settings for ElikoWandCommandSink.

    `led_pulse_pattern_hex` is the bare hex string passed to Eliko's
    SET_TAG_LEDH command (no `0x` prefix, no leading `$PEKIO`).
    """

    led_pulse_pattern_hex: str
