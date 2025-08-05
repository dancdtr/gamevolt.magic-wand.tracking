import os
import time
import tkinter as tk

from PIL import Image, ImageTk


class SpellDisplay:
    """
    Creates a Tkinter window displaying spell images/animations
    loaded from disk, selectable by spell name.
    Supports clearing the screen to a blank white display.
    """

    def __init__(self, spells_dir: str, size_x: int = 1130, size_y: int = 1280):
        """
        :param spells_dir: Directory containing spell image files (e.g., 'fireball.png').
        :param size: Pixel size (width and height) of the display window.
        """
        self.spells_dir = spells_dir

        # Initialize Tkinter window
        self.root = tk.Tk()
        self.root.title("Spell Display")
        self.root.geometry(f"{size_x}x{size_y}")
        self.label = tk.Label(self.root, bg="white")
        self.label.pack(expand=True, fill=tk.BOTH)

        # Load all spell images into a dict
        self.images = {}
        for fname in os.listdir(self.spells_dir):
            name, ext = os.path.splitext(fname)
            if ext.lower() in (".png", ".gif", ".jpg", ".jpeg"):
                path = os.path.join(self.spells_dir, fname)
                img = Image.open(path)
                img = img.resize((size_x, size_y))
                # Bind image to this root explicitly
                self.images[name] = ImageTk.PhotoImage(img, master=self.root)

        # Prepare a blank white image for clearing the display
        blank = Image.new("RGB", (size_x, size_y), (255, 255, 255))
        self.blank_image = ImageTk.PhotoImage(blank, master=self.root)

    def show(self, spell_name: str | None) -> None:
        """
        Display the image corresponding to spell_name.
        :param spell_name: Base filename (without extension) of the spell image.
        """
        if spell_name == None:
            self.show_white()
            return

        time.sleep(0.25)
        img = self.images.get(spell_name)
        if img:
            self.label.config(image=img, text="", bg="white")
            self.label.image = img  # prevent garbage collection
        else:
            # Spell not found: show placeholder text
            self.label.config(text=f"Spell '{spell_name}' not found", image="", bg="white")
            self.label.image = None
        self.root.update_idletasks()

    def show_white(self) -> None:
        """
        Clears the display to a blank white screen.
        """
        self.label.config(image=self.blank_image, text="", bg="white")
        self.label.image = self.blank_image
        self.root.update_idletasks()

    def run(self) -> None:
        """
        Starts the Tkinter main loop.
        """
        self.root.mainloop()
