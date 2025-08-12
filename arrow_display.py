import math
import os
import tkinter as tk

from PIL import Image, ImageTk

from classification.axis import Axis
from classification.gesture_type import GestureType as G


class ArrowDisplay:
    """
    Tkinter window displaying gesture icons loaded from files,
    transforming them (rotate/mirror) for all Gesture enum values.
    """

    def __init__(self, size: int = 1000, assets_dir: str = "./gestures"):
        self.size = size
        self.assets_dir = assets_dir
        self.root = tk.Tk()
        self.root.title("Wand Gesture Display")
        self.root.geometry(f"{size}x{size}")
        self.label = tk.Label(self.root)
        self.label.pack(expand=True)

        # Load base images
        self.base_images = {
            "cardinal": Image.open(os.path.join(self.assets_dir, "cardinal.png")),
            "intercardinal": Image.open(os.path.join(self.assets_dir, "intercardinal.png")),
            "semi": Image.open(os.path.join(self.assets_dir, "semi.png")),
            "none": Image.open(os.path.join(self.assets_dir, "none.png")),
            "unknown": Image.open(os.path.join(self.assets_dir, "unknown.png")),
            "circle": Image.open(os.path.join(self.assets_dir, "circle.png")),
        }

        # Pre-generate transformed images for each gesture
        self.images: dict[G, ImageTk.PhotoImage] = {}
        for gesture in G:
            img = self._create_image(gesture)
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            self.images[gesture] = ImageTk.PhotoImage(img)

    def show(self, gesture: G) -> None:
        img = self.images.get(gesture)
        if img:
            self.label.config(image=img)
            self.root.update_idletasks()

    def run(self) -> None:
        # no mainloop; updates via show()
        pass

    def _create_image(self, gesture: G) -> Image.Image:
        if gesture == G.NONE:
            base = self.base_images["none"]
            return base
        if gesture == G.UNKNOWN:
            base = self.base_images["unknown"]
            return base

        name = gesture.name.lower()
        if name.endswith("_circle"):
            base = self.base_images["circle"]
            semi_mapping: dict[G, tuple[int, Axis | None]] = {
                G.UP_START_CW_CIRCLE: (0, None),
                G.RIGHT_START_CW_CIRCLE: (270, None),
                G.DOWN_START_CW_CIRCLE: (180, None),
                G.LEFT_START_CW_CIRCLE: (90, None),
                G.UP_START_CCW_CIRCLE: (0, Axis.X),
                G.RIGHT_START_CCW_CIRCLE: (270, Axis.X),
                G.DOWN_START_CCW_CIRCLE: (180, Axis.X),
                G.LEFT_START_CCW_CIRCLE: (90, Axis.X),
            }
            angle, flip_direction = semi_mapping.get(gesture, (0, None))
            img = base.rotate(angle, expand=True)

            if flip_direction == Axis.X:
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif flip_direction == Axis.Y:
                img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

            return img

        if name.endswith("_semi"):
            base = self.base_images["semi"]
            semi_mapping: dict[G, tuple[int, Axis | None]] = {
                G.UP_VIA_RIGHT_SEMI: (0, Axis.X),
                G.UP_VIA_LEFT_SEMI: (0, None),
                G.RIGHT_VIA_DOWN_SEMI: (270, Axis.Y),
                G.LEFT_VIA_DOWN_SEMI: (90, None),
                G.RIGHT_VIA_UP_SEMI: (270, None),
                G.LEFT_VIA_UP_SEMI: (90, Axis.Y),
                G.DOWN_VIA_RIGHT_SEMI: (180, None),
                G.DOWN_VIA_LEFT_SEMI: (180, Axis.X),
            }
            angle, flip_direction = semi_mapping.get(gesture, (0, None))
            img = base.rotate(angle, expand=True)

            if flip_direction == Axis.X:
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif flip_direction == Axis.Y:
                img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

            return img

        if any(name == d for d in ("up", "down", "left", "right")):
            base = self.base_images["cardinal"]
            angle_map = {"up": 90, "right": 0, "down": 270, "left": 180}
            angle = angle_map[name]
            return base.rotate(angle, expand=True)
        else:
            base = self.base_images["intercardinal"]
            angle_map = {"up_left": 90, "up_right": 0, "down_right": 270, "down_left": 180}
            angle = angle_map[name]
            return base.rotate(angle, expand=True)
