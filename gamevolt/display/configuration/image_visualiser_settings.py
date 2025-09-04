from dataclasses import dataclass


@dataclass
class ImageVisualiserSettings:
    width: int
    height: int
    title: str
    gui_fps: int = 60

    @property
    def fps(self) -> int:
        return max(1, self.gui_fps)
