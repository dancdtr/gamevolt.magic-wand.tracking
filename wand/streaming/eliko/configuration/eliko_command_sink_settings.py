from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class ElikoCommandSinkSettings(SettingsBase):
    """Settings for ElikoWandCommandSink.

    `led_pulse_color` names one of the `Color` enum members (RED, GREEN, BLUE,
    WHITE, YELLOW, MAGENTA, CYAN, RGB). Multi-bit forms can be expressed by
    pipe-joining (e.g. "RED|GREEN") — parsed in the sink.
    """

    led_pulse_color: str
