from gamevolt.configuration.appsetting import appsetting
from visualisation.coordinate_mode import CoordinateMode


@appsetting
class TrailSettings:
    scale: float
    render_scale: float  # draw-only zoom about widget centre; does not touch data/clip
    max_points: int
    draw_points: bool
    line_width: int
    point_radius: int
    smooth: bool
    line_colour: str  # tail / base colour
    fade: bool  # comet fade: older tail points dissolve + taper to make the trail magical
    tail_alpha: float  # alpha (0..1) at the oldest tail point when fade is on
    glow: bool  # soft wide glow underlay behind the trail + a bright tip sparkle
    glow_width: int  # extra pixels of width for the glow halo around the core line
    gradient: bool  # blend colour along the trail from line_colour (tail) to head_colour (head)
    head_colour: str  # colour at the newest/head end when gradient is on
    coords_mode: CoordinateMode  # "centered" = [-1..1], origin at centre
    y_up: bool  # True => +Y up (top), False => screen down
    clip_to_bounds: bool  # clamp input coords into valid range
    pixel_margin: int  # inner padding (pixels)
