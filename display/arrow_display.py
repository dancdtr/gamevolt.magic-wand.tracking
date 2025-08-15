import os
import tkinter as tk

from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType as GestureType
from display.image_providers.cardinal_line_image_provider import CardinalLineImageProvider
from display.image_providers.debug_image_provider import DebugImageProvider
from display.image_providers.image_provider import ImageProvider
from display.image_providers.intercardinal_line_image_provider import IntercardinalLineImageProvider
from display.image_providers.secondary_intercardinal_line_image_provider import SecondaryIntercardinalLineImageProvider


class ArrowDisplay:
    """
    Tkinter window displaying gesture icons loaded from files,
    transforming them (rotate/mirror) for all Gesture enum values.
    """

    def __init__(self, image_size: int = 1000, assets_dir: str = "./display/images/primitives"):
        self.size = image_size
        self.assets_dir = assets_dir
        self.root = tk.Tk()
        self.root.title("Wand Gesture Display")
        self.root.geometry(f"{image_size}x{image_size}")
        self.label = tk.Label(self.root)
        self.label.pack(expand=True)

        def build_path(png) -> str:
            return os.path.join(assets_dir, png)

        self.image_providers: list[ImageProvider] = [
            DebugImageProvider(build_path("unknown.png"), build_path("none.png"), image_size),
            CardinalLineImageProvider(build_path("cardinal_line.png"), image_size),
            IntercardinalLineImageProvider(build_path("intercardinal_line.png"), image_size),
            SecondaryIntercardinalLineImageProvider(build_path("secondary_intercardinal_line.png"), image_size),
        ]

    def show(self, type: GestureType) -> None:
        img = self._get_image(type)
        if img:
            self.label.config(image=img)
            self.root.update_idletasks()

    def _get_image(self, type: GestureType) -> PhotoImage:
        for image_provider in self.image_providers:
            image = image_provider.get_image(type)
            if image is not None:
                return image

        raise Exception(f"No image to display for gesture: '{type}'!")
