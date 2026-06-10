from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class ElikoCommandSinkSettings(SettingsBase):
    """Settings for ElikoWandCommandSink.

    `idle_colour` names a `Colour` enum member (RED, GREEN, BLUE, WHITE,
    YELLOW, MAGENTA, CYAN, RGB, WARM_WHITE, ...). Multi-bit forms via
    pipe-join ("RED|GREEN") — parsed in the sink. Rendered as a slow fade
    by the sink while a wand is active (zone-present).

    Pulse colours are passed per-call to `WandCommandSink.pulse`.
    """

    idle_colour: str
