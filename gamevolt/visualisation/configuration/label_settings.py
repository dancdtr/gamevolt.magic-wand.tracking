from dataclasses import dataclass
from enum import Enum, auto

from gamevolt.configuration.settings_base import SettingsBase


class LabelSide(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()


class LabelFillType(Enum):
    NONE = auto()
    X = auto()
    Y = auto()
    BOTH = auto()


@dataclass
class LabelSettings(SettingsBase):
    text: str
    foreground_colour: str
    background_colour: str
    side: LabelSide
    fill: LabelFillType
