from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from visualisation.coordinate_mode import CoordinateMode


@dataclass
class TrailColourSettings(SettingsBase):
    line_color: str
    point_colour: str


@dataclass
class TrailSettings(SettingsBase):
    max_points: int
    draw_points: bool
    line_width: int
    point_radius: int
    smooth: bool
    coords_mode: CoordinateMode  # "centered" = [-1..1], origin at centre
    y_up: bool  # True => +Y up (top), False => screen down
    clip_to_bounds: bool  # clamp input coords into valid range
    pixel_margin: int  # inner padding (pixels)


@dataclass
class VisualiserInputSettings:
    coords_mode: CoordinateMode  # "centered" = [-1..1], origin at centre
    y_up: bool  # True => +Y up (top), False => screen down
    clip_to_bounds: bool  # clamp input coords into valid range
    pixel_margin: int  # inner padding (pixels)
