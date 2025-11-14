from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from visualisation.coordinate_mode import CoordinateMode


@dataclass
class InputTrailVisualiserSettings(SettingsBase):
    line_width: int = 2
    line_color: str = "#5eead4"
    draw_points: bool = False
    point_radius: int = 3
    point_colour: str | None = None
    smooth: bool = False
    coords_mode: CoordinateMode = CoordinateMode.CENTRED  # "centered" = [-1..1], origin at centre
    y_up: bool = True  # True => +Y up (top), False => screen down
    clip_to_bounds: bool = True  # clamp input coords into valid range
    pixel_margin: int = 0  # optional inner padding (pixels)
