from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from visualisation.coordinate_mode import CoordinateMode


@dataclass
class InputVisualiserSettings(SettingsBase):
    trail_max_points: int
    show_axes: bool
    axes_color: str
    axes_width: int
    line_width: int
    line_color: str
    draw_points: bool
    point_radius: int
    point_colour: str | None
    smooth: bool
    coords_mode: CoordinateMode  # "centered" = [-1..1], origin at centre
    y_up: bool  # True => +Y up (top), False => screen down
    clip_to_bounds: bool  # clamp input coords into valid range
    pixel_margin: int  # inner padding (pixels)
