import math
import tkinter as tk

from PIL import Image, ImageDraw, ImageTk


class ArrowDisplay:
    """
    Creates a Tkinter window displaying a larger arrow with a rectangular body
    and triangular head, on a white background, supporting 8 cardinal and intercardinal directions.
    """

    def __init__(self, size: int = 300):
        self.size = size
        self.root = tk.Tk()
        self.root.title("Wand Gesture Arrow")
        self.root.geometry(f"{size}x{size}")
        self.label = tk.Label(self.root)
        self.label.pack(expand=True)

        # Define all eight directions
        self.directions = ["up", "up-right", "right", "down-right", "down", "down-left", "left", "up-left"]

        # Pre-generate arrow images for each direction
        self.images = {dir: self._make_arrow(dir) for dir in self.directions}

    def _make_arrow(self, direction: str) -> ImageTk.PhotoImage:
        """
        Draws an arrow with a rectangular body and triangular head pointing in `direction`
        on a white background.
        """
        img = Image.new("RGBA", (self.size, self.size), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        cx, cy = self.size // 2, self.size // 2
        length = self.size * 0.4
        head_length = length * 0.4
        body_length = length * 0.6
        head_width = length * 0.6
        body_width = length * 0.2

        # Base shapes for "up" arrow
        rect = [
            (cx - body_width / 2, cy + body_length / 2),
            (cx + body_width / 2, cy + body_length / 2),
            (cx + body_width / 2, cy - body_length / 2),
            (cx - body_width / 2, cy - body_length / 2),
        ]
        tri = [
            (cx, cy - length),
            (cx - head_width / 2, cy - body_length / 2),
            (cx + head_width / 2, cy - body_length / 2),
        ]

        # Map each direction to its rotation angle
        angle_map = {
            "up": 0,
            "up-right": 45,
            "right": 90,
            "down-right": 135,
            "down": 180,
            "down-left": 225,
            "left": 270,
            "up-left": 315,
        }
        angle = math.radians(angle_map[direction])

        def rotate(point):
            dx, dy = point[0] - cx, point[1] - cy
            xr = dx * math.cos(angle) - dy * math.sin(angle) + cx
            yr = dx * math.sin(angle) + dy * math.cos(angle) + cy
            return (xr, yr)

        rect_rot = list(map(rotate, rect))
        tri_rot = list(map(rotate, tri))

        # Draw filled shapes
        draw.polygon(rect_rot, fill="black")
        draw.polygon(tri_rot, fill="black")

        return ImageTk.PhotoImage(img)

    def show(self, direction: str) -> None:
        """
        Updates the displayed arrow. Supports 8 directions.
        """
        img = self.images.get(direction)
        if img:
            self.label.config(image=img)
            self.root.update_idletasks()

    def run(self) -> None:
        """
        Placeholder: no separate mainloop; updates happen via update() calls.
        """
        pass
