from gamevolt.configuration.appsetting import appsetting
from visualisation.coordinate_mode import CoordinateMode


@appsetting
class TrailColourSettings:
    line_colour: str
    point_colour: str


@appsetting
class TrailSettings:
    scale: float
    max_points: int
    draw_points: bool
    line_width: int
    point_radius: int
    smooth: bool
    coords_mode: CoordinateMode  # "centered" = [-1..1], origin at centre
    y_up: bool  # True => +Y up (top), False => screen down
    clip_to_bounds: bool  # clamp input coords into valid range
    pixel_margin: int  # inner padding (pixels)


@appsetting
class VisualiserInputSettings:
    coords_mode: CoordinateMode  # "centered" = [-1..1], origin at centre
    y_up: bool  # True => +Y up (top), False => screen down
    clip_to_bounds: bool  # clamp input coords into valid range
    pixel_margin: int  # inner padding (pixels)
