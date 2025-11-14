from dataclasses import dataclass, field

from gamevolt.configuration.settings_base import SettingsBase
from visualisation.configuration.input_trail_visualiser_settings import InputTrailVisualiserSettings
from visualisation.coordinate_mode import CoordinateMode


@dataclass
class InputVisualiserSettings(SettingsBase):
    trail_max_points: int = 64
    show_axes: bool = True
    axes_color: str = "#9ca3af"
    axes_width: int = 1
    tk_wand_trail_renderer: InputTrailVisualiserSettings = field(
        default_factory=lambda: InputTrailVisualiserSettings(
            line_width=3,
            line_color="#22d3ee",
            draw_points=True,
            coords_mode=CoordinateMode.CENTRED,  # expects [-1..1] from MouseTkInput
            y_up=True,
        )
    )
