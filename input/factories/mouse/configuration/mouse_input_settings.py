from dataclasses import dataclass

from preview import TkPreviewSettings


@dataclass
class MouseInputSettings:
    sample_frequency: int
    invert_x: bool
    invert_y: bool
